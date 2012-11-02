#---------------------------------------------------------------
# Project         : adminkit
# File            : fedora.py
# Copyright       : (C) 2012 Frederic Lepied
# Author          : Frederic Lepied
# Created On      : Thu Nov  1 00:12:55 2012
# Purpose         : Fedora specific interfaces
#---------------------------------------------------------------

import commands
import glob

class System:
    def get_packages(self):
        status, output = commands.getstatusoutput("rpm -qa --qf '%{NAME}\n'")
        return output.split('\n')

    def install_package(self, pkg):
        status, output = commands.getstatusoutput('yum install -y %s' % pkg)
        return (status, output)
    
    def activate_service(self, service, debug, dryrun):
        if len(glob.glob('/etc/rc3.d/S*%s' % service)) == 0:
            status, output = commands.getstatusoutput('chkconfig --add %s; service %s start' % (service, service))
            return (status, output)
        else:
            return (0, '')
        
    def deactivate_service(self, service, debug, dryrun):
        if len(glob.glob('/etc/rc3.d/S*%s' % service)) != 0:
            status, output = commands.getstatusoutput('service %s stop; chkconfig --del %s' % (service, service))
            return (status, output)
        else:
            return (0, '')
        
# fedora.py ends here
