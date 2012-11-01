#---------------------------------------------------------------
# Project         : adminkit
# File            : generic.py
# Copyright       : (C) 2012 Frederic Lepied
# Author          : Frederic Lepied
# Created On      : Thu Nov  1 20:14:18 2012
# Purpose         : Generic interfaces in case we don't have specific ones.
#---------------------------------------------------------------

class System:
    def get_packages(self):
        return []

    def install_package(self, pkg):
        return (0, '')
    
# generic.py ends here
