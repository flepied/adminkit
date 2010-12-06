#---------------------------------------------------------------
# Project         : adminkit
# File            : debian.py
# Copyright       : (C) 2010 Frederic Lepied
# Author          : Frederic Lepied
# Created On      : Mon Dec  6 21:32:22 2010
# Purpose         : debian specific class
#---------------------------------------------------------------

import commands

class System:
    def get_packages(self):
        status, output = commands.getstatusoutput("dpkg -l|grep ^ii|awk '{print $2;}'")
        return output.split('\n')

    def install_pkg(self, pkg):
        status, output = commands.getstatusoutput('apt-get install %s' % pkg)
        return (status, output)
    
# debian.py ends here
