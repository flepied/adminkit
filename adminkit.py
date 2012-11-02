#---------------------------------------------------------------
# Project         : adminkit
# File            : adminkit.py
# Copyright       : (C) 2010 Splitted-Desktop Systems
#                   (C) 2010,2011,2012 Frederic Lepied
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
try:
    import commands
except ImportError:
    import subprocess
    commands = subprocess
    
import socket
import sys
import getopt
import imp
import hashlib
import pwd
import grp
import logging
import logging.handlers
import codecs

from jinja2 import Environment, FileSystemLoader

STRING_TYPE = type('e')

_DEBUG = False
_DRY_RUN = False
_FORCE = False
_RET = 0

_ENV = None

_ROOT = '/var/lib/adminkit'
_DEST = '/'
_ONCE_DIR = os.path.join(_ROOT, 'once')
_VARS_FILE = os.path.join(_ROOT, 'vars')

#######################################################################################
# Accessor needed by external modules
#######################################################################################

def debug():
    """Accessor."""
    return _DEBUG

def root():
    """Accessor."""
    return _ROOT

def dest():
    """Accessor."""
    return _DEST

##################################################
# Logging config
##################################################
logger = None

#######################################################################################

def detect_os():
    """Detect the OS using lsb_release."""
    return commands.getoutput("lsb_release -a 2>/dev/null|grep Distributor|sed -n 's/Distributor ID:\s*//p'").lower()

def detect_os_code():
    """Detect OS codename using lsb_release."""
    return commands.getoutput("lsb_release -c|sed 's/Codename:\s*//'")


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
        fd = codecs.open(dst, 'w', 'utf-8')
        os.chmod(dst, mode)
        if uid != -1 or gid != -1:
            os.chown(dst, uid, gid)
        fd.write(result)
        fd.close()
        return dst

def is_newer(f1, f2):
    """Check if a f1 is newer than f2."""
    if _FORCE or not os.path.exists(f2):
        return True
    else:
        return (os.path.getmtime(f1) >= os.path.getmtime(f2))

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

def global_conf(conf):
    """Process the config file again with another driver called global."""
    (path, _name) = os.path.split(os.path.realpath(sys.argv[0]))
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

def expand_variables(str_, plan):
    """Expand variable in the string using jinja2."""
    return _ENV.from_string(str_).render(plan.var)

def manage_pkgs(plan, system):
    """Manage system packages."""
    if len(plan.pkg) > 0:
        installed_pkgs = system.get_packages()
        for p in plan.pkg:
            if p in installed_pkgs:
                logger.debug('%s already installed', p)
            else:
                status, output = system.install_package(p)
                if status == 0:
                    logger.info('installed package %s', p)
                else:
                    logger.error('problems installing package % :\n%s', p, output)
                    return 1
    return 0

def manage_dirs(plan):
    """Manage directory creation."""
    for path in plan.get_dirs():
        d = expand_variables(os.path.join(_DEST, path[1:]), plan)
        if not os.path.isdir(d):
            logger.info('creating directory %s', d)
            os.makedirs(d)
        else:
            logger.debug('%s already exists', d)
    return 0

def manage_files(plan, strings):
    """Manage the creation of files from templates."""
    ret = 0
    check_vars(plan.var, _VARS_FILE)
    modified = []
    for f in plan.get_files():
        uid = -1
        gid = -1
        if type(f) == STRING_TYPE:
            mode = 0o644
        else:
            mode = f[1]
            if len(f) >= 3 and f[2] != None:
                try:
                    uid = pwd.getpwnam(f[2]).pw_uid
                except KeyError:
                    logger.error('Unable to find uid for %s', f[2])
                    ret = 1
            if len(f) >= 4 and f[3] != None:
                try:
                    gid = grp.getgrnam(f[3]).gr_gid
                except KeyError:
                    logger.error('Unable to find gid for %s', f[3])
                    ret = 1
            f = f[0]
                
        l = find_file_with_vars(f, os.path.join(_ROOT, 'files'), strings + plan.get_roles())
        if l:
            t = expand_variables(os.path.join(_DEST, f[1:]), plan)
            if is_newer(l, t) or is_newer(_VARS_FILE, t):
                if copyfile(l, t, plan.var, mode, uid, gid):
                    modified.append(f)
                    logger.info('copied %s to %s', l, t)
                else:
                    logger.info('touched %s', t)
            else:
                logger.debug('%s not newer than %s', l, t)
        else:
            logger.error('ERROR %s not found', f)
            ret = 1
    return ret, modified

def manage_perms(plan):
    """Manage permissions of files and directories."""
    ret = 0
    for f in plan.get_perms():
        try:
            s = os.stat(f[0])
            if s[0] & 0o7777 != f[1]:
                logger.info('Changing mode of %s from 0%o to 0%o', f[0], s[0] & 0o7777, f[1])
                os.chmod(f[0], f[1])
        except:
            logger.error('ERROR changing perms of %s:\n%s', f[0], sys.exc_info()[1])
            ret = 1
    return ret

def manage_services(plan, modified, system):
    """Manage services."""
    ret = 0
    
    for s in plan.get_services():
        if s[1]:
            system.activate_service(s[0], _DEBUG, _DRY_RUN)
        else:
            system.deactivate_service(s[0], _DEBUG, _DRY_RUN)

    reloaded = []
    for f in modified:
        try:
            for s in plan.get_file_for_service(f):
                if s not in reloaded:
                    reloaded.append(s)
                    logger.info('reloading service %s', s)
                    if not _DRY_RUN:
                        status, output = commands.getstatusoutput('/etc/init.d/%s reload || /etc/init.d/%s restart' % (s, s))
                        if status != 0:
                            logger.error('Error reloading %s:\n%s', s, output)
                            ret = 1
            for r in plan.command.keys():
                if r.search(f):
                    cmd = plan.get_command(r)
                    logger.info('launching command %s for %s', cmd, f)
                    if not _DRY_RUN:
                        status, output = commands.getstatusoutput(cmd)
                        if status != 0:
                            logger.error('Error reloading %s:\n%s', cmd, output)
                            ret = 1
        except KeyError:
            pass

    return ret

def manage_onces(plan):
    """Manage commands that needs to be launched only once."""
    ret = 0
    for cmd in plan.get_onces():
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
                    ret = 1
    return ret


def manage_pidfiles(plan):
    """Manage pid files to check that services are present else relaunch them."""
    ret = 0
    for p in plan.pidfile.keys():
        restart = False
        if not os.path.exists(plan.get_pidfile(p)):
            restart = False
        else:
            fd = open(plan.get_pidfile(p))
            content = fd.read(-1)
            fd.close()
            if len(content) == 0:
                restart = True
            elif content[-1] == '\n':
                content = content[:-1]
            if not os.path.exists('/proc/' + content):
                restart = True
        if restart:
            logger.info('Restarting service %s', p)
            if not _DRY_RUN:
                status, output = commands.getstatusoutput('/etc/init.d/%s restart' % (p,))
                if status != 0:
                    logger.error('Error restarting %s:\n%s', p, output)
                    ret = 1
    return ret

def init_system(plan):
    """Initialize the system object according to the OS detection."""
    for s in (plan.get_var('oscode'), plan.get_var('osname'), 'generic'):
        try:
            mod = __import__(s)
            break
        except ImportError:
            continue
    return mod.System()

def init_roles(plan):
    """Run role files to fill the plan."""
    global _ENV

    ret = 0
    path = []    
    strings = []
    for p in plan.var.values() + plan.get_roles() + ['']:
        if not type(p) == STRING_TYPE:
            continue
        strings.append(p)
        d = os.path.join(_ROOT, 'roles', p)
        if os.path.exists(d) and os.path.isdir(d):
            path.append(d)

    _ENV = Environment(loader = FileSystemLoader([os.path.join(_ROOT, 'files'), '/']))
    
    if _DEBUG:
        logger.debug('PATH -> %s', path)
        for c in plan.var.keys():
            logger.debug('%s -> %s', c, plan.get_var(c))
        logger.debug('ROLES -> %s', plan.get_roles())
        logger.debug('ROOT -> %s', _ROOT)
        logger.debug('DEST -> %s', _DEST)
        logger.debug('VARS_FILE -> %s', _VARS_FILE)
        logger.debug('ONCE_DIR -> %s', _ONCE_DIR)
       
    # exported functions to be used in role files
    functions = {'add_files': plan.add_files,
                 'files_for_service': plan.files_for_service,
                 'files_to_command': plan.files_to_command,
                 'check_service_by_pidfile': plan.check_service_by_pidfile,
                 'check_perms': plan.check_perms,
                 'add_dirs': plan.add_dirs,
                 'add_var': plan.add_var,
                 'add_to_list': plan.add_to_list,
                 'get_var': plan.get_var,
                 'run_once': plan.run_once,
                 'install_pkg': plan.install_pkg,
                 'global_conf': global_conf,
                 'activate_service': plan.activate_service,
                 'deactivate_service': plan.deactivate_service,
                 }

    plan.add_var('roles', plan.get_roles())
    
    for c in plan.get_roles():
        logger.debug('Loading role %s', c)
        f = find_file(c, path)
        if f:
            execfile(f, functions)
        else:
            logger.error('No such role %s in %s', c, ':'.join(path))
            ret = 1
    
    logger.debug(_ENV.from_string('hostname is {{ hostname }}').render(plan.var))
    logger.debug('FILES %s', plan.get_files())
    logger.debug('SERVICES %s', plan.service)
    logger.debug('FILES_FOR_SERVICES %s', plan.file_for_service)
    logger.debug('VARIABLES %s', plan.var)
    logger.debug('ONCE %s', plan.get_onces())
    logger.debug('PKGS %s', plan.get_pkgs())
    
    return ret, path, strings

def finalize(plan):
    """Do the actual action that were registered for the host."""
    
    system = init_system(plan)
    
    ret, path, strings = init_roles(plan)
    
    ret += manage_pkgs(plan, system)

    ret += manage_dirs(plan)
    
    ret2, modified = manage_files(plan, strings)
    ret += ret2

    ret += manage_perms(plan)

    ret += manage_services(plan, modified, system)

    ret += manage_pidfiles(plan)

    ret += manage_onces(plan)
    
    return ret

def set_root(rt):
    """Initialize global variables."""
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
    print("%s [-h|-H <hostname>|-V <variable:value>|-r <role>|-R <root>|-D <dest>|-d|-s|-n|-f|<config file>]" % sys.argv[0])
    
# process command line

def init(plan):
    """Initialize variables."""
    global _DEBUG, _DRY_RUN, logger, _FORCE

    # hack to allow arguments to be passed after the magic #! (they are passed as a single arg)
    if len(sys.argv) > 1:
        argv = sys.argv[1].split(' ') + sys.argv[2:]
    else:
        argv = sys.argv[1:]
        
    try:
        opts, args = getopt.getopt(argv, "fdnhH:r:R:D:V:s",
                                   ["force", "debug", "dry-run", "help", "hostname=", 'role=', 'rootdir=', 'destdir=', 'var=', 'syslog'])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err)) # will print something like "option -a not recognized"
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
        elif o in ("-f", "--force"):
            _FORCE=True
        elif o in ("-n", "--dry-run"):
            _DRY_RUN = True
        elif o in ("-H", "--hostname"):
            _HOST = a
        elif o in ("-V", "--var"):
            k, v = a.split(':', 1)
            plan.add_var(k, v)
        elif o in ("-r", "--role"):
            plan.add_roles(_HOST, a)
        elif o in ("-R", "--rootdir"):
            set_root(a)
        elif o in ("-D", "--destdir"):
            set_dest(a)
        elif o in ('-s', '--syslog'):
            syslog = True
        else:
            assert False, "unhandled option"

    logger = logging.getLogger("adminkit")
    
    if syslog:
        h = logging.handlers.SysLogHandler('/dev/log', 'syslog')
        f = logging.Formatter('adminkit[%(process)d]: %(message)s')
        h.setFormatter(f)
    else:
        h = logging.StreamHandler()
    logger.addHandler(h)
    
    if _DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    h = _HOST.split('.', 1)
    _SHORT = h[0]
    if len(h) > 1:
        _DOMAIN = h[1]
    else:
        _DOMAIN = ''

    plan.add_var('shortname', _SHORT)
    plan.add_var('hostname', _HOST)
    plan.add_var('domainname', _DOMAIN)
    plan.add_var('osname', _OS)
    plan.add_var('sysname', _SYSTEM)
    plan.add_var('oscode', _CODE)
    
    if len(args) == 1:
        path = os.path.abspath(args[0])
        return path
    else:
        return os.path.join(_ROOT, 'adminkit.conf')

# adminkit.py ends here
