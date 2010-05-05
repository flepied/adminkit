#---------------------------------------------------------------
# Project         : adminkit
# File            : adminkit.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Mon Jan 11 21:03:44 2010
# Purpose         : 
#---------------------------------------------------------------

import os
import string
import commands
import re
import socket
import sys
import getopt
import imp

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
_SERVICES = {}
_SYSTEM = ''
_CODE = ''
_DEFAULT_DOMAIN = False
_ACTIONS = []
_PIDFILE = {}
_PERMS = []

class Template(string.Template):
    delimiter = '@'

def detect_os():
    return 'debian'

def define_domain(dom):
    global _DEFAULT_DOMAIN

    _DEFAULT_DOMAIN = dom

    return _DEFAULT_DOMAIN

def add_var(host, name, val):
    global _VARS
    
    if '.' not in host:
        host = host + '.' + _DEFAULT_DOMAIN
    if host == _HOST:
        _VARS[name] = val

def add_roles(host, *roles):
    global _HOST, _ROLES
    
    if '.' not in host:
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
    content = open(src).read(-1)
    result = Template(content).substitute(vars)
    basename = os.path.dirname(dst)
    if not os.path.exists(basename):
	os.makedirs(basename)
    f = open(dst, 'w')
    os.chmod(dst, mode)
    f.write(result)
    f.close()
    
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

def check_perms(*files):
    global _PERMS
    _PERMS = _PERMS + list(files)

def is_newer(f1, f2):
    if not os.path.exists(f2):
        return True
    else:
        return (os.path.getmtime(f1) > os.path.getmtime(f2))

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
    for p in _VARS.values() + _ROLES + ['']:
        d = os.path.join(_ROOT, 'roles', p)
        if os.path.exists(d) and os.path.isdir(d):
            path.append(d)
    
    if _DEBUG:
        print path
        for c in _VARS.keys():
            print c, '->', _VARS[c]

    # exported functions to be used in role files
    globals = {'add_files': add_files,
               'files_for_service': files_for_service,
               'check_service_by_pidfile': check_service_by_pidfile,
               'check_perms': check_perms,
               }
    
    for c in _ROLES:
        if _DEBUG:
            print 'Loading role', c
        f = find_file(c, path)
        execfile(f, globals)
    
    if _DEBUG:
        print Template('hostname is @hostname').substitute(_VARS)
        print 'FILES', _FILES
        print 'SERVICES', _SERVICES
        print 'VARIABLES', _VARS

    # Managing files
    modified = []
    for f in _FILES:
        if type(f) == type('a'):
            mode = 0644
        else:
            mode = f[1]
            f = f[0]
        l = find_file_with_vars(f, os.path.join(_ROOT, 'files'), _VARS.values() + _ROLES)
        t = os.path.join(_DEST, f[1:])
        if l:
            if is_newer(l, t):
                print 'copying', l, 'to', t
                copyfile(l, t, _VARS, mode)
                modified.append(f)
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
            
def usage():
    print "%s [-h|-H <hostname>|-V <variable:value>|-r <role>|-R <root>|-D <dest>|-c <configfile>|-d]" % sys.argv[0]
    
# process command line

def init():
    global _OS, _SHORT, _DOMAIN, _HOST, _ROOT, _DEST, _SYSTEM, _DEBUG, _CODE
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "dhc:H:r:R:D:V:",
                                   ["debug", "help", "config=", "hostname=", 'role=', 'root=', 'dest=', 'var='])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    cfgdir = '/var/lib/adminkit'

    _OS = detect_os()
    _HOST = socket.gethostname()
    _SHORT = _HOST.split('.')[0]
    _DOMAIN = _HOST.split('.', 1)[1]
    _SYSTEM = os.uname()[0].lower()
    _CODE = '%s-%s' % (_OS, commands.getoutput("lsb_release -c|sed 's/Codename:\s*//'"))
    
    add_var(_HOST, 'shortname', _SHORT)
    add_var(_HOST, 'hostname', _HOST)
    add_var(_HOST, 'domainname', _DOMAIN)
    add_var(_HOST, 'osname', _OS)
    add_var(_HOST, 'sysname', _SYSTEM)
    add_var(_HOST, 'oscode', _CODE)

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
            add_var(_HOST, k, v)
        elif o in ("-r", "--role"):
            add_roles(_HOST, a)
        elif o in ("-R", "--root"):
            _ROOT = a
        elif o in ("-D", "--dest"):
            _DEST = a
        elif o in ("-c", "--config"):
            cfgdir = a
        else:
            assert False, "unhandled option"
        
    return cfgdir

# adminkit.py ends here
