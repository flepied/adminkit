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
        commands.getstatusoutput('apt-get update -q')
        status, output = commands.getstatusoutput("dpkg -l|grep ^ii|awk '{print $2;}'")
        return output.split('\n')

    def install_package(self, pkg):
        status, output = commands.getstatusoutput('apt-get install -q -y %s' % pkg)
        return (status, output)
    
# debian.py ends here
