#---------------------------------------------------------------
# Project         : adminkit
# File            : fedora.py
# Copyright       : (C) 2012 by 
# Author          : Frederic Lepied
# Created On      : Thu Nov  1 00:12:55 2012
# Purpose         : 
#---------------------------------------------------------------

import commands

class System:
    def get_packages(self):
        status, output = commands.getstatusoutput("rpm -qa --qf '%{NAME}\n'")
        return output.split('\n')

    def install_package(self, pkg):
        status, output = commands.getstatusoutput('yum install -y %s' % pkg)
        return (status, output)
    
# fedora.py ends here
