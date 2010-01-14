#---------------------------------------------------------------
# Project         : adminkit
# File            : adminkit.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Mon Jan 11 21:03:44 2010
# Purpose         : 
#---------------------------------------------------------------

import shutil
import os
import fnmatch
import string
import commands
import re
import filecmp
import socket
import sys
import getopt
import imp

_DEBUG = False

_SHORT = False
_HOST = False
_VARS = {}
_ROLES = []
_ROOT = '/var/lib/adminkit'
_DEST = '/'
_OS = False
_FILES = []
_SERVICES = {}

class Template(string.Template):
    delimiter = '@'

def detect_os():
    return 'debian'

def add_var(host, name, val):
    if host == _SHORT:
        _VARS[name] = val
    
def add_role(host, cl):
    global _SHORT
    
    if host == _SHORT:
        _ROLES.append(cl)

def findfile(filename, path, vars):
    basename = os.path.join(path, filename[1:])
    for v in vars:
        fullname = basename + '.' + v
        if os.path.exists(fullname):
            return fullname
    if os.path.exists(basename):
        return basename
    return None

def copyfile(src, dst, vars):
    content = open(src).read(-1)
    result = Template(content).substitute(vars)
    f = open(dst, 'w')
    f.write(result)
    f.close()
    
def add_files(*files):
    global _FILES
    _FILES = _FILES + list(files)

def files_for_service(service, *files):
    for f in files:
        try:
            _SERVICES[f] = _SERVICES[f] + [service]
        except KeyError:
            _SERVICES[f] = [service]

def is_newer(f1, f2):
    if not os.path.exists(f2):
        return True
    else:
        return (os.path.getmtime(f1) > os.path.getmtime(f2))

def finalize():
    path = []
    for p in _VARS.values() + _ROLES + ['']:
        path.append(os.path.join(_ROOT, 'rules', p))
    if _DEBUG:
        print path
        for c in _VARS.keys():
            print c, '->', _VARS[c]
    for c in _ROLES:
        if _DEBUG:
            print 'Loading role', c
        try:
            module = sys.modules[c] # already imported?
        except KeyError:
            file, pathname, description = imp.find_module(c, path)
            module = imp.load_module(c, file, pathname, description)
        
    if _DEBUG:
        print Template('hostname is @hostname').substitute(_VARS)
        print 'FILES', _FILES
        print 'SERVICES', _SERVICES
        print 'VARIABLES', _VARS

    modified = []
    for f in _FILES:
        l = findfile(f, os.path.join(_ROOT, 'files'), _VARS.values() + _ROLES)
        t = os.path.join(_DEST, f[1:])
        if l:
            if is_newer(l, t):
                print 'copying', l, 'to', t
                copyfile(l, t, _VARS)
                modified.append(f)
            else:
                if _DEBUG:
                    print l, 'not newer than', t
        else:
            print 'ERROR', t, 'not found'

    for f in modified:
        try:
            for s in _SERVICES[f]:
                print 'reloading service', s
                status, output = commands.getstatusoutput('/etc/init.d/%s reload || /etc/init.d/%s restart' % (s, s))
                if status != 0:
                    print 'Error reloading %s:' % s
                    print output
        except KeyError:
            pass
        
def usage():
    print "%s [-h|-H <hostname>|-C <role:value>]" % sys.argv[0]
    
# process command line

def init():
    global _OS, _SHORT, _DOMAIN, _HOST, _ROOT, _DEST
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "dhc:H:r:R:D:",
                                   ["debug", "help", "config=", "hostname=", 'role=', 'root=', 'dest='])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    cfgdir = '/etc/adminkit'
    output = None
    verbose = False
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--debug"):
            _DEBUG = True
        elif o in ("-H", "--hostname"):
            _HOST = a
        elif o in ("-r", "--role"):
            k,v = a.split(':', 1)
            add_var(k, v)
        elif o in ("-R", "--root"):
            _ROOT = a
        elif o in ("-D", "--dest"):
            _DEST = a
        elif o in ("-c", "--config"):
            cfgdir = a
        else:
            assert False, "unhandled option"
    
    #_debug = True
    _debug = False

    if not _OS:
        _OS = detect_os()
        
    # Store default values
    if not _HOST:
        _HOST = socket.gethostname()
        
    _SHORT = _HOST.split('.')[0]
    _DOMAIN = _HOST.split('.', 1)[1]

    add_var(_SHORT, 'shortname', _SHORT)
    add_var(_SHORT, 'hostname', _HOST)
    add_var(_SHORT, 'domainname', _DOMAIN)
    add_var(_SHORT, 'osname', _OS)

    return cfgdir

# adminkit.py ends here
