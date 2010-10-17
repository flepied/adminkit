#---------------------------------------------------------------
# Project         : adminkit
# File            : adminkit.py
# Copyright       : Splitted-Desktop Systems, 2010
#                   Frederic Lepied, 2010
# Author          : Frederic Lepied
# Created On      : Mon Jan 11 21:03:44 2010
# Purpose         : main functions
#---------------------------------------------------------------

import os
import string
import commands
import re
import socket
import sys
import getopt
import imp
import hashlib

from jinja2 import Environment

_ENV = Environment()

STRING_TYPE = type('e')

_DEBUG = False

_SHORT = False
_HOST = False
_DOMAIN = ''
_VARS = {}
_ROLES = []
_ROOT = '/var/lib/adminkit'
_DEST = '/'
_OS = False
_FILES = []
_DIRS = []
_SERVICES = {}
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

def detect_os():
    return commands.getoutput("lsb_release -a 2>/dev/null|grep Distributor|sed -n 's/Distributor ID:\s*//p'").lower()

def detect_os_code():
    return commands.getoutput("lsb_release -c|sed 's/Codename:\s*//'")

def define_domain(dom):
    global _DEFAULT_DOMAIN

    _DEFAULT_DOMAIN = dom

    return _DEFAULT_DOMAIN

def add_var_host(host, name, val):
    global _VARS
    
    if '.' not in host and _DEFAULT_DOMAIN:
        host = host + '.' + _DEFAULT_DOMAIN
    
    if host == _HOST:
        add_var(name, val)

def add_var(name, val):
    _VARS[name] = val
    
def add_to_list_host(host, name, val):
    global _VARS
    
    if '.' not in host and _DEFAULT_DOMAIN:
        host = host + '.' + _DEFAULT_DOMAIN
    
    if host == _HOST:
        add_to_list(name, val)
        
def add_to_list(name, val):
    try:
        _VARS[name].append(val)
    except KeyError:
        _VARS[name] = [val,]

def get_var(name):
    try:
        return _VARS[name]
    except KeyError:
        return None
    
def add_roles(host, *roles):
    global _HOST, _ROLES
    
    if '.' not in host and _DEFAULT_DOMAIN:
        host = host + '.' + _DEFAULT_DOMAIN
    
    if host == _HOST:
        for role in roles:
            if role not in _ROLES:
                _ROLES.append(role)

def find_file_with_vars(filename, path, vars):
    basename = os.path.join(path, filename[1:])
    for v in vars:
        fullname = basename + '.' + v
        if os.path.exists(fullname):
            return fullname
    if os.path.exists(basename):
        return basename
    return None

def find_file(basename, path):
    for dir in path:
        f = os.path.join(dir, basename)
        if os.path.exists(f):
            return f
    return None

def copyfile(src, dst, vars, mode):
    '''Instanciate a template and write it to a new file.

    Arguments:
    src: path to the jinja2 template
    dst: path to the destination file
    vars: associative array representing the variables to expand in the template
    mode: permissions for the destination file
    
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
    result = template.render(vars)
    basedir = os.path.dirname(dst)
    if not os.path.exists(basedir):
	os.makedirs(basedir)
    if result == orig:
        os.utime(dst, None)
        return False
    else:
        f = open(dst, 'w')
        os.chmod(dst, mode)
        f.write(result)
        f.close()
        return True

def add_files(*files):
    global _FILES
    _FILES = _FILES + list(files)

def files_for_service(service, *files):
    add_files(*files)
    for f in files:
        try:
            _SERVICES[f] = _SERVICES[f] + [service]
        except KeyError:
            _SERVICES[f] = [service]

def add_dirs(*dirs):
    global _DIRS
    _DIRS = _DIRS + list(dirs)

def check_perms(*files):
    global _PERMS
    _PERMS = _PERMS + list(files)

def run_once(command):
    global _ONCE
    _ONCE.append(command)

def files_to_command(command, *list):
    global _COMMANDS
    for r in list:
        _COMMANDS[re.compile(r)] = command

def is_newer(f1, f2):
    if not os.path.exists(f2):
        return True
    else:
        return (os.path.getmtime(f1) > os.path.getmtime(f2))

def check_vars(vars, path):
    '''checks that vars has not changed. A checksum is compared to the content
    of the file pointed by path. If the content has changed, the file is rewritten
    with the new checksum.'''
    s = hashlib.sha1(str(vars)).hexdigest()
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
    try:
        return sys.modules[c] # already imported?
    except KeyError:
        file, pathname, description = imp.find_module(c, path)
        return imp.load_module(c, file, pathname, description)

def check_service_by_pidfile(service, pidfile):
    _PIDFILE[service] = pidfile

def finalize():
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
    
    if _DEBUG:
        print 'PATH ->', path
        for c in _VARS.keys():
            print c, '->', _VARS[c]
        print 'ROLES ->', _ROLES
        print 'ROOT ->', _ROOT
        print 'DEST ->', _DEST
        
    # exported functions to be used in role files
    globals = {'add_files': add_files,
               'files_for_service': files_for_service,
               'check_service_by_pidfile': check_service_by_pidfile,
               'check_perms': check_perms,
               'add_dirs': add_dirs,
               'add_var': add_var,
               'add_to_list': add_to_list,
               'get_var': get_var,
               'run_once': run_once,
               'files_for_service': files_for_service,
               }
    
    for c in _ROLES:
        if _DEBUG:
            print 'Loading role', c
        f = find_file(c, path)
        execfile(f, globals)
    
    if _DEBUG:
        print _ENV.from_string('hostname is {{ hostname }}').render(_VARS)
        print 'FILES', _FILES
        print 'SERVICES', _SERVICES
        print 'VARIABLES', _VARS
        print 'ONCE', _ONCE

    # Managing directories
    for d in _DIRS:
        dir = os.path.join(_DEST, d[1:])
        if not os.path.isdir(dir):
            print 'creating directory', dir
            os.makedirs(dir)
        else:
            if _DEBUG:
                print dir, 'already exists'
            
    # Managing files
    check_vars(_VARS, _VARS_FILE)
    modified = []
    for f in _FILES:
        if type(f) == STRING_TYPE:
            mode = 0644
        else:
            mode = f[1]
            f = f[0]
        l = find_file_with_vars(f, os.path.join(_ROOT, 'files'), strings + _ROLES)
        t = os.path.join(_DEST, f[1:])
        if l:
            if is_newer(l, t) or is_newer(_VARS_FILE, t):
                if copyfile(l, t, _VARS, mode):
                    modified.append(f)
                    print 'copied', l, 'to', t
                else:
                    print 'touched', t
            else:
                if _DEBUG:
                    print l, 'not newer than', t
        else:
            print 'ERROR', t, 'not found'

    for f in _PERMS:
        try:
            s = os.stat(f[0])
            if s[0] & 07777 != f[1]:
                print 'Changing mode of %s from 0%o to 0%o' % (f[0], s[0] & 07777, f[1])
                os.chmod(f[0], f[1])
        except:
            print 'ERROR changing perms of', f[0], ':'
            print sys.exc_info()[1]
    
    # Managing services
    reloaded = []
    for f in modified:
        try:
            for s in _SERVICES[f]:
                if s not in reloaded:
                    reloaded.append(s)
                    print 'reloading service', s
                    status, output = commands.getstatusoutput('/etc/init.d/%s reload || /etc/init.d/%s restart' % (s, s))
                    if status != 0:
                        print 'Error reloading %s:' % s
                        print output
            for r in _COMMANDS.keys():
                if r.search(f):
                    cmd = _COMMANDS[r]
                    print 'launching command', s, 'for', f
                    status, output = commands.getstatusoutput(cmd)
                    if status != 0:
                        print 'Error reloading %s:' % cmd
                        print output
        except KeyError:
            pass

    for p in _PIDFILE.keys():
        restart = False
        if not os.path.exists(_PIDFILE[p]):
            restart = True
        else:
            file = open(_PIDFILE[p])
            content = file.read(-1)
            file.close()
            if content[-1] == '\n':
                content = content[:-1]
            if not os.path.exists('/proc/' + content):
                restart = True
        if restart:
            print 'Restarting service', p
            status, output = commands.getstatusoutput('/etc/init.d/%s restart' % (p,))
            if status != 0:
                print 'Error restarting %s:' % p
                print output
    for cmd in _ONCE:
        hash = hashlib.sha1(cmd).hexdigest()
        f = os.path.join(_ONCE_DIR, hash)
        if not os.path.exists(f):
            print 'Running once', cmd
            status, output = commands.getstatusoutput(cmd)
            if status == 0:
                open(f, 'w').close()
            else:
                print 'Error running once %s:' % cmd
                print output
                    
def set_root(root):
    global _ROOT

    _ROOT = root

def set_dest(dest):
    global _DEST

    _DEST = dest

def usage():
    print "%s [-h|-H <hostname>|-V <variable:value>|-r <role>|-R <root>|-D <dest>|-d|<config file>]" % sys.argv[0]
    
# process command line

def init():
    global _OS, _SHORT, _DOMAIN, _HOST, _ROOT, _DEST, _SYSTEM, _DEBUG, _CODE

    # hack to allow arguments to be passed after the magic #! (they are passed as a single arg)
    if len(sys.argv) > 1:
        argv = sys.argv[1].split(' ') + sys.argv[2:]
    else:
        argv = sys.argv[1:]
        
    try:
        opts, args = getopt.getopt(argv, "dhH:r:R:D:V:",
                                   ["debug", "help", "hostname=", 'role=', 'rootdir=', 'destdir=', 'var='])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    
    _OS = detect_os()
    _HOST = socket.gethostname()
    h = _HOST.split('.', 1)
    _SHORT = h[0]
    if len(h) > 1:
        _DOMAIN = h[1]
    else:
        _DOMAIN = ''
    _SYSTEM = os.uname()[0].lower()
    _CODE = detect_os_code()
    
    add_var('shortname', _SHORT)
    add_var('hostname', _HOST)
    add_var('domainname', _DOMAIN)
    add_var('osname', _OS)
    add_var('sysname', _SYSTEM)
    add_var('oscode', _CODE)
    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--debug"):
            _DEBUG = True
        elif o in ("-H", "--hostname"):
            _HOST = a
        elif o in ("-V", "--var"):
            k,v = a.split(':', 1)
            add_var(k, v)
        elif o in ("-r", "--role"):
            add_roles(_HOST, a)
        elif o in ("-R", "--rootdir"):
            set_root(a)
        elif o in ("-D", "--destdir"):
            set_dest(a)
        else:
            assert False, "unhandled option"

    if len(args) == 1:
        file = os.path.abspath(args[0])
        set_root(os.path.dirname(file))
        return file
    else:
        return os.path.join(_ROOT, 'adminkit.conf')

# adminkit.py ends here
