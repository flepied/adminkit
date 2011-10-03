#---------------------------------------------------------------
# Project         : adminkit
# File            : adminkit.py
# Copyright       : (C) 2010 Splitted-Desktop Systems
#                   (C) 2010,2011 Frederic Lepied
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Author          : Frederic Lepied
# Created On      : Mon Jan 11 21:03:44 2010
# Purpose         : main functions
#---------------------------------------------------------------

""" AdminKit main module.
"""

import os
import commands
import re
import socket
import sys
import getopt
import imp
import hashlib
import pwd
import grp
import logging
import logging.config

from jinja2 import Environment, FileSystemLoader

STRING_TYPE = type('e')

_DEBUG = False
_DRY_RUN = False
_RET = 0

_ENV = None

_SHORT = False
_HOST = ''
_DOMAIN = ''
_VARS = {}
_ROLES = []
_ROOT = '/var/lib/adminkit'
_DEST = '/'
_OS = False
_FILES = []
_DIRS = []
_FILES_FOR_SERVICES = {}
_SERVICES = []
_SYSTEM = ''
_CODE = ''
_DEFAULT_DOMAIN = False
_ACTIONS = []
_PIDFILE = {}
_PERMS = []
_ONCE = []
_COMMANDS = {}
_ONCE_DIR = os.path.join(_ROOT, 'once')
_VARS_FILE = os.path.join(_ROOT, 'vars')
_PKGS = []

##################################################
# Logging config
##################################################
logger = None

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'normal': {
            'format': '%(message)s',
        },
        'syslogfmt': {
            'format': 'adminkit[%(process)d]: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'normal',
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'syslogfmt',
            'facility': 'syslog',
            'address': '/dev/log',
        },
    },
    'loggers': {
        'syslog': {
            'handlers':['syslog'],
            'propagate': True,
            'level':'INFO',
        },
        'console': {
            'handlers':['console'],
            'propagate': True,
            'level':'INFO',
        },
    }
}

#######################################################################################
# Accessor needed by external modules
#######################################################################################

def debug():
    """Accessor."""
    return _DEBUG

def root():
    """Accessor."""
    return _ROOT

def default_domain():
    """Accessor."""
    return _DEFAULT_DOMAIN

def dest():
    """Accessor."""
    return _DEST

#######################################################################################

def detect_os():
    """Detect the OS using lsb_release."""
    return commands.getoutput("lsb_release -a 2>/dev/null|grep Distributor|sed -n 's/Distributor ID:\s*//p'").lower()

def detect_os_code():
    """Detect OS codename using lsb_release."""
    return commands.getoutput("lsb_release -c|sed 's/Codename:\s*//'")

def define_domain(dom):
    """Define the default domain name."""
    global _DEFAULT_DOMAIN

    _DEFAULT_DOMAIN = dom

    return _DEFAULT_DOMAIN

def check_host(host):
    """Check if host if the local host."""
    if '.' not in host and _DEFAULT_DOMAIN:
        host = host + '.' + _DEFAULT_DOMAIN
    
    return (host == _HOST)
    
def add_var_host(host, name, *val):
    """Define a variable named name to the value val if host is the current host."""
    if check_host(host):
        add_var(name, *val)

ARRAY_TYPE = type({})

def add_to(tab, *val):
    """Helper function for add_var."""
    if len(val) == 1:
        return val[0]
    else:
        try:
            tab[val[0]] = add_to(tab[val[0]], *val[1:])
        except:
            tab[val[0]] = add_to({}, *val[1:])
        return tab

def add_var(*val):
    """Define a variable named name to the value val."""
    add_to(_VARS, *val)
    
def add_to_list_host(host, name, val):
    """Add val to the list named name if host if the current host."""
    if check_host(host):
        add_to_list(name, val)
        
def add_to_list(name, val):
    """Add val to the list named name."""
    try:
        _VARS[name].append(val)
    except KeyError:
        _VARS[name] = [val, ]

def get_var(name):
    """Return the value of variable name or None if it's undefined."""
    try:
        return _VARS[name]
    except KeyError:
        return None
    
def add_roles(host, *roles):
    """Add roles for the host."""
    if check_host(host):
        for role in roles:
            if role not in _ROLES:
                _ROLES.append(role)

def find_file_with_vars(filename, path, variables):
    """Lookup a file called filename in path using extensions from variables."""
    basename = os.path.join(path, filename[1:])
    for var in variables:
        fullname = basename + '.' + var
        if os.path.exists(fullname):
            return fullname
    if os.path.exists(basename):
        return basename
    return None

def find_file(basename, paths):
    """Lookup a file in a set of path."""
    for directory in paths:
        path = os.path.join(directory, basename)
        if os.path.exists(path):
            return path
    return None

def copyfile(src, dst, variables, mode, uid, gid):
    '''Instanciate a template and write it to a new file.

    Arguments:
    src: path to the jinja2 template
    dst: path to the destination file
    variables: associative array representing the variables to expand in the template
    mode: permissions for the destination file
    uid: user id
    gid: group id
    
    Return value: boolean to indicate if the content has changed or not
    
    If the content has not changed, the destination file has just its
    access and modifed date changed.
    '''
    if os.path.exists(dst):
        orig = open(dst).read(-1)
    else:
        orig = None
    content = open(src).read(-1)
    template = _ENV.from_string(content)
    result = template.render(variables)
    basedir = os.path.dirname(dst)
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    if result == orig:
        os.utime(dst, None)
        return False
    else:
        fd = open(dst, 'w')
        os.chmod(dst, mode)
        if uid != -1 or gid != -1:
            os.chown(dst, uid, gid)
        fd.write(result)
        fd.close()
        return dst

def add_files(*files):
    """Add files to the global list."""
    global _FILES
    _FILES = _FILES + list(files)

def files_for_service(service, *files):
    """Add files to the global list and register these files to be monitored for
the service."""
    add_files(*files)
    for path in files:
        try:
            _FILES_FOR_SERVICES[path] = _FILES_FOR_SERVICES[path] + [service]
        except KeyError:
            _FILES_FOR_SERVICES[path] = [service]

def add_dirs(*dirs):
    """Add directories to the global list."""
    global _DIRS
    _DIRS = _DIRS + list(dirs)

def check_perms(*files):
    """Add permissions to check to the global list."""
    global _PERMS
    _PERMS = _PERMS + list(files)

def run_once(command):
    """Add a command to be run once to the global list."""
    _ONCE.append(command)

def files_to_command(command, *li):
    """Register regular expressions on modified files to run the command."""
    for regexp in li:
        _COMMANDS[re.compile(regexp)] = command

def is_newer(f1, f2):
    """Check if a f1 is newer than f2."""
    if not os.path.exists(f2):
        return True
    else:
        return (os.path.getmtime(f1) > os.path.getmtime(f2))

def check_vars(variables, path):
    '''checks that vars has not changed. A checksum is compared to the content
    of the file pointed by path. If the content has changed, the file is rewritten
    with the new checksum.'''
    s = hashlib.sha1(str(variables)).hexdigest()
    if os.path.exists(path):
        f = open(path)
        s2 = f.read(-1)
        f.close()
    else:
        s2 = None
    if s != s2:
        f = open(path, 'w')
        f.write(s)
        f.close()
        return False
    else:
        return True

def import_module(c, path):
    """Import a module from path."""
    try:
        return sys.modules[c] # already imported?
    except KeyError:
        fd, pathname, description = imp.find_module(c, path)
        return imp.load_module(c, fd, pathname, description)

def check_service_by_pidfile(service, pidfile):
    """Add pidfile to the global checks for service."""
    _PIDFILE[service] = pidfile

def install_pkg(*pkgs):
    """Add packages to the global list of packages to install."""
    for p in pkgs:
        if not p in _PKGS:
            _PKGS.append(p)

def global_conf(conf):
    """Process the config file again with another driver called global."""
    (path, _name) = os.path.split(sys.argv[0])
    if path != '':
        cmd = '%s/global ' % path
    else:
        cmd = 'global '
    
    cmd = cmd + conf + ' ' + ' '.join(sys.argv[1:])
    
    logger.debug('Global config through %s', cmd)
    
    (res, out) = commands.getstatusoutput(cmd)
    if res != 0:
        global _RET
        logger.error('Error running "%s":\n%s', cmd, out)
        _RET = 1
    else:
        logger.info(out)
        
    return res

def expand_variables(s):
    """Expand variable in the string using jinja2."""
    return _ENV.from_string(s).render(_VARS)

def activate_service(name):
    """Add the service to the list of services to be activated."""
    global _SERVICES

    _SERVICES.append((name, True))
    
def deactivate_service(name):
    """Add the service to the list of services to be deactivated."""
    global _SERVICES

    _SERVICES.append((name, False))
    
def finalize():
    """Do the actual action that were registered for the host."""

    global _ENV
    global _RET
    
    _RET = 0                             # return value
    
    for s in (_CODE, _OS):
        try:
            mod = __import__(s)
            break
        except ImportError:
            continue
    system = mod.System()
    # Loading roles
    path = []    
    strings = []
    for p in _VARS.values() + _ROLES + ['']:
        if not type(p) == STRING_TYPE:
            continue
        strings.append(p)
        d = os.path.join(_ROOT, 'roles', p)
        if os.path.exists(d) and os.path.isdir(d):
            path.append(d)

    _ENV = Environment(loader = FileSystemLoader([os.path.join(_ROOT, 'files'), '/']))
    
    if _DEBUG:
        logger.debug('PATH -> %s', path)
        for c in _VARS.keys():
            logger.debug('%s -> %s', c, _VARS[c])
        logger.debug('ROLES -> %s', _ROLES)
        logger.debug('ROOT -> %s', _ROOT)
        logger.debug('DEST -> %s', _DEST)
        logger.debug('VARS_FILE -> %s', _VARS_FILE)
        logger.debug('ONCE_DIR -> %s', _ONCE_DIR)
       
    # exported functions to be used in role files
    functions = {'add_files': add_files,
                 'files_for_service': files_for_service,
                 'files_to_command': files_to_command,
                 'check_service_by_pidfile': check_service_by_pidfile,
                 'check_perms': check_perms,
                 'add_dirs': add_dirs,
                 'add_var': add_var,
                 'add_to_list': add_to_list,
                 'get_var': get_var,
                 'run_once': run_once,
                 'install_pkg': install_pkg,
                 'global_conf': global_conf,
                 'activate_service': activate_service,
                 'deactivate_service': deactivate_service,
                 }
    
    for c in _ROLES:
        logger.debug('Loading role %s', c)
        f = find_file(c, path)
        if f:
            execfile(f, functions)
        else:
            logger.error('No such role %s in %s', c, ':'.join(path))
            _RET = 1
    
    logger.debug(_ENV.from_string('hostname is {{ hostname }}').render(_VARS))
    logger.debug('FILES %s', _FILES)
    logger.debug('SERVICES %s', _SERVICES)
    logger.debug('FILES_FOR_SERVICES %s', _FILES_FOR_SERVICES)
    logger.debug('VARIABLES %s', _VARS)
    logger.debug('ONCE %s', _ONCE)
    logger.debug('PKGS %s', _PKGS)

    # manage pkgs
    if len(_PKGS) > 0:
        installed_pkgs = system.get_packages()
        for p in _PKGS:
            if p in installed_pkgs:
                logger.debug('%s already installed', p)
            else:
                status, output = system.install_package(p)
                if status == 0:
                    logger.info('installed package %s', p)
                else:
                    logger.error('problems installing package % :\n%s', p, output)
                    _RET = 1

    # Managing directories
    for path in _DIRS:
        d = expand_variables(os.path.join(_DEST, path[1:]))
        if not os.path.isdir(d):
            logger.info('creating directory %s', d)
            os.makedirs(d)
        else:
            logger.debug('%s already exists', d)
            
    # Managing files
    check_vars(_VARS, _VARS_FILE)
    modified = []
    for f in _FILES:
        uid = -1
        gid = -1
        if type(f) == STRING_TYPE:
            mode = 0644
        else:
            mode = f[1]
            if len(f) >= 3 and f[2] != None:
                try:
                    uid = pwd.getpwnam(f[2]).pw_uid
                except KeyError:
                    logger.error('Unable to find uid for %s', f[2])
                    _RET = 1
            if len(f) >= 4 and f[3] != None:
                try:
                    gid = grp.getgrnam(f[3]).gr_gid
                except KeyError:
                    logger.error('Unable to find gid for %s', f[3])
                    _RET = 1
            f = f[0]
                
        l = find_file_with_vars(f, os.path.join(_ROOT, 'files'), strings + _ROLES)
        if l:
            t = expand_variables(os.path.join(_DEST, f[1:]))
            if is_newer(l, t) or is_newer(_VARS_FILE, t):
                if copyfile(l, t, _VARS, mode, uid, gid):
                    modified.append(f)
                    logger.info('copied %s to %s', l, t)
                else:
                    logger.info('touched %s', t)
            else:
                logger.debug('%s not newer than %s', l, t)
        else:
            logger.error('ERROR %s not found', f)
            _RET = 1

    for f in _PERMS:
        try:
            s = os.stat(f[0])
            if s[0] & 07777 != f[1]:
                logger.info('Changing mode of %s from 0%o to 0%o', f[0], s[0] & 07777, f[1])
                os.chmod(f[0], f[1])
        except:
            logger.error('ERROR changing perms of %s:\n%s', f[0], sys.exc_info()[1])
            _RET = 1
    
    # Managing services

    for s in _SERVICES:
        if s[1]:
            system.activate_service(s[0], _DEBUG, _DRY_RUN)
        else:
            system.deactivate_service(s[0], _DEBUG, _DRY_RUN)
            
    reloaded = []
    for f in modified:
        try:
            for s in _FILES_FOR_SERVICES[f]:
                if s not in reloaded:
                    reloaded.append(s)
                    logger.info('reloading service %s', s)
                    if not _DRY_RUN:
                        status, output = commands.getstatusoutput('/etc/init.d/%s reload || /etc/init.d/%s restart' % (s, s))
                        if status != 0:
                            logger.error('Error reloading %s:\n%s', s, output)
                            _RET = 1
        except KeyError:
            pass
        for r in _COMMANDS.keys():
            if r.search(f):
                cmd = _COMMANDS[r]
                logger.info('launching command %s for %s', cmd, f)
                if not _DRY_RUN:
                    status, output = commands.getstatusoutput(cmd)
                    if status != 0:
                        logger.error('Error reloading %s:\n%s', cmd, output)
                        _RET = 1
                    
    for p in _PIDFILE.keys():
        restart = False
        if not os.path.exists(_PIDFILE[p]):
            restart = False
        else:
            fd = open(_PIDFILE[p])
            content = fd.read(-1)
            fd.close()
            if content[-1] == '\n':
                content = content[:-1]
            if not os.path.exists('/proc/' + content):
                restart = True
        if restart:
            logger.info('Restarting service %s', p)
            if not _DRY_RUN:
                status, output = commands.getstatusoutput('/etc/init.d/%s restart' % (p,))
                if status != 0:
                    logger.error('Error restarting %s:\n%s', p, output)
                    _RET = 1
    for cmd in _ONCE:
        hsh = hashlib.sha1(cmd).hexdigest()
        path = os.path.join(_ONCE_DIR, hsh)
        if not os.path.exists(path):
            logger.info('Running once %s', cmd)
            if not _DRY_RUN:
                status, output = commands.getstatusoutput(cmd)
                if status == 0:
                    open(path, 'w').close()
                else:
                    logger.error('Error running once %s:\n%s', cmd, output)
                    _RET = 1
    return _RET

def set_root(rt):
    "Initialize global variables."""
    global _ROOT
    global _ONCE_DIR
    global _VARS_FILE

    _ROOT = rt
    _ONCE_DIR = os.path.join(_ROOT, 'once')
    _VARS_FILE = os.path.join(_ROOT, 'vars')

def set_dest(dst):
    """Initialize destination directory."""
    global _DEST

    _DEST = dst

def usage():
    """Help message."""
    print "%s [-h|-H <hostname>|-V <variable:value>|-r <role>|-R <root>|-D <dest>|-d|<config file>]" % sys.argv[0]
    
# process command line

def init():
    """Initialize variables."""
    global _OS, _SHORT, _DOMAIN, _HOST, _SYSTEM, _DEBUG, _CODE, _DRY_RUN, logger

    # hack to allow arguments to be passed after the magic #! (they are passed as a single arg)
    if len(sys.argv) > 1:
        argv = sys.argv[1].split(' ') + sys.argv[2:]
    else:
        argv = sys.argv[1:]
        
    try:
        opts, args = getopt.getopt(argv, "dnhH:r:R:D:V:s",
                                   ["debug", "dry-run", "help", "hostname=", 'role=', 'rootdir=', 'destdir=', 'var=', 'syslog'])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    
    _OS = detect_os()
    _HOST = socket.gethostname()
    _SYSTEM = os.uname()[0].lower()
    _CODE = detect_os_code()

    syslog = False
    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--debug"):
            _DEBUG=True
        elif o in ("-n", "--dry-run"):
            _DRY_RUN = True
        elif o in ("-H", "--hostname"):
            _HOST = a
        elif o in ("-V", "--var"):
            k, v = a.split(':', 1)
            add_var(k, v)
        elif o in ("-r", "--role"):
            add_roles(_HOST, a)
        elif o in ("-R", "--rootdir"):
            set_root(a)
        elif o in ("-D", "--destdir"):
            set_dest(a)
        elif o in ('-s', '--syslog'):
            syslog = True
        else:
            assert False, "unhandled option"

    logging.config.dictConfig(LOGGING)
    if syslog:
        logger = logging.getLogger('syslog')
    else:
        logger = logging.getLogger('console')

    if _DEBUG:
        logger.setLevel(logging.DEBUG)
        
    h = _HOST.split('.', 1)
    _SHORT = h[0]
    if len(h) > 1:
        _DOMAIN = h[1]
    else:
        _DOMAIN = ''

    add_var('shortname', _SHORT)
    add_var('hostname', _HOST)
    add_var('domainname', _DOMAIN)
    add_var('osname', _OS)
    add_var('sysname', _SYSTEM)
    add_var('oscode', _CODE)
    
    if len(args) == 1:
        path = os.path.abspath(args[0])
        return path
    else:
        return os.path.join(_ROOT, 'adminkit.conf')

# adminkit.py ends here
