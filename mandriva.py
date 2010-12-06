#---------------------------------------------------------------
# Project         : adminkit
# File            : mandriva.py
# Copyright       : (C) 2010 by Frederic Lepied
# Author          : Frederic Lepied
# Created On      : Mon Dec  6 22:03:23 2010
# Purpose         : mandriva specific class
#---------------------------------------------------------------

import commands

class System:
    def get_packages(self):
        commands.getstatusoutput('urpmi.update -a')
        status, output = commands.getstatusoutput("rpm -qa --qf '%{NAME}\n'")
        return output.split('\n')

    def install_package(self, pkg):
        status, output = commands.getstatusoutput('urpmi --auto %s' % pkg)
        return (status, output)

# mandriva.py ends here
