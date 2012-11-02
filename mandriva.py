#---------------------------------------------------------------
# Project         : adminkit
# File            : mandriva.py
# Copyright       : (C) 2010 by Frederic Lepied
# Author          : Frederic Lepied
# Created On      : Mon Dec  6 22:03:23 2010
# Purpose         : mandriva specific class
#---------------------------------------------------------------

import commands
import glob

class System:
    def get_packages(self):
        commands.getstatusoutput('urpmi.update -a')
        status, output = commands.getstatusoutput("rpm -qa --qf '%{NAME}\n'")
        return output.split('\n')

    def install_package(self, pkg):
        status, output = commands.getstatusoutput('urpmi --auto %s' % pkg)
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

# mandriva.py ends here
