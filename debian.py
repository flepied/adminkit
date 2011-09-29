#---------------------------------------------------------------
# Project         : adminkit
# File            : debian.py
# Copyright       : (C) 2010 Frederic Lepied
# Author          : Frederic Lepied
# Created On      : Mon Dec  6 21:32:22 2010
# Purpose         : debian specific class
#---------------------------------------------------------------

import commands
import glob

class System:
    def get_packages(self):
        commands.getstatusoutput('apt-get update -q')
        status, output = commands.getstatusoutput("dpkg -l|grep ^ii|awk '{print $2;}'")
        return output.split('\n')

    def install_package(self, pkg):
        status, output = commands.getstatusoutput('apt-get install -q -y %s' % pkg)
        return (status, output)

    def activate_service(self, service, debug, dryrun):
        if len(glob.glob('/etc/rc2.d/S*%s' % service)) == 0:
            cmd = 'update-rc.d %s defaults; invoke-rc.d %s start' % (service, service)
            print 'activating service', service, 'with', cmd
            if not dryrun:
                status, output = commands.getstatusoutput(cmd)
                if debug:
                    print output
                return (status, output)
        return (0, '')
        
    def deactivate_service(self, service, debug, dryrun):
        if len(glob.glob('/etc/rc2.d/S*%s' % service)) != 0:
            cmd = 'invoke-rc.d %s stop; update-rc.d -f %s remove' % (service, service)
            print 'deactivating service', service, 'with', cmd
            if not dryrun:
                status, output = commands.getstatusoutput(cmd)
                if debug:
                    print output
                return (status, output)
        return (0, '')
        
# debian.py ends here
