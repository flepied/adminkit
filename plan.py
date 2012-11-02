#---------------------------------------------------------------
# Project         : adminkit
# File            : plan.py
# Copyright       : (C) 2012 Frederic Lepied
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Author          : Frederic Lepied
# Created On      : Tue Oct 30 22:33:08 2012
# Purpose         : Plan class represents what will be enforced later
#---------------------------------------------------------------

import re

class PlanMeta(type):
    '''PlanMeta metaclass create accessors based on the __list__ and __assoc__ class fields'''
    
    def __init__(cls, name, bases, dct):
        super(PlanMeta, cls).__init__(name, bases, dct)
        for k in dct['__list__']:
            cls.create_list_accessors(k)
        for k in dct['__assoc__']:
            cls.create_assoc_accessors(k)

    def create_list_accessors(cls, name):
        def get(self):
            return getattr(self, name)
        get.__name__ = 'get_' + name + 's'
        setattr(cls, get.__name__, get)
        def set(self, val):
            getattr(self, name).append(val)
        set.__name__ = 'add_' + name
        setattr(cls, set.__name__, set)

    def create_assoc_accessors(cls, name):
        def get(self, key):
            return getattr(self, name)[key]
        get.__name__ = 'get_' + name
        setattr(cls, get.__name__, get)
        def set(self, key, val):
            getattr(self, name)[key] = val
        set.__name__ = 'add_' + name
        setattr(cls, set.__name__, set)

DEFAULT_DOMAIN = 'default_domain'

class Plan(object):
    '''Plan stores the plan to be enforced later'''
    
    __metaclass__ = PlanMeta
    __list__ = ('pkg', 'role', 'file', 'dir', 'action', 'perm', 'once', 'service')
    __assoc__ = ('file_for_service', 'pidfile', 'command')
    
    def __init__(self):
        for k in Plan.__list__:
            setattr(self, k, [])
        for k in Plan.__assoc__:
            setattr(self, k, {})
        self.var = {DEFAULT_DOMAIN: None, 'hostname': None}
        
    def define_domain(self, dom):
        """Define the default domain name."""
    
        self.var[DEFAULT_DOMAIN] = dom
    
        return dom

    def default_domain(self):
        """Accessor."""
        return self.get_var(DEFAULT_DOMAIN)
    
    def check_host(self, host):
        """Check if host if the local host."""
        if '.' not in host and self.var[DEFAULT_DOMAIN]:
            host = host + '.' + self.var[DEFAULT_DOMAIN]
        
        return (host == self.var['hostname'])
        
    def add_var_host(self, host, name, *val):
        """Define a variable named name to the value val if host is the current host."""
        if self.check_host(host):
            self.add_var(name, *val)

    def add_to(self, tab, *val):
        """Helper function for add_var."""
        if len(val) == 1:
            return val[0]
        else:
            try:
                tab[val[0]] = self.add_to(tab[val[0]], *val[1:])
            except:
                tab[val[0]] = self.add_to({}, *val[1:])
            return tab
    

    def add_var(self, *val):
        """Define a variable named name to the value val."""
        self.add_to(self.var, *val)
        
    def add_to_list_host(self, host, name, val):
        """Add val to the list named name if host if the current host."""
        if self.check_host(host):
            self.add_to_list(name, val)
            
    def add_to_list(self, name, val):
        """Add val to the list named name."""
        try:
            self.var[name].append(val)
        except KeyError:
            self.var[name] = [val, ]
    
    def get_var(self, name):
        """Return the value of variable name or None if it's undefined."""
        try:
            return self.var[name]
        except KeyError:
            return None
        
    def add_roles(self, host, *roles):
        """Add roles for the host."""
        if self.check_host(host):
            for role in roles:
                if role not in self.get_roles():
                    self.add_role(role)

    def add_files(self, *files):
        """Add files to the global list."""
        for f in files:
            self.add_file(f)
    
    def files_for_service(self, service, *files):
        """Add files to the global list and register these files to be monitored for
    the service."""
        self.add_files(*files)
        for path in files:
            try:
                self.file_for_service[path].append(service)
            except KeyError:
                self.file_for_service[path] = [service, ]
    
    def add_dirs(self, *dirs):
        """Add directories to the global list."""
        for d in dirs:
            self.add_dir(d)
    
    def check_perms(self, *files):
        """Add permissions to check to the global list."""
        for f in files:
            self.add_perm(f)
    
    def run_once(self, command):
        """Add a command to be run once to the global list."""
        self.add_once(command)
    
    def files_to_command(self, command, *files):
        """Add files to the global list and register these files to run
        the command when modified."""
        self.add_files(*files)
        for file_ in files:
            self.add_command(file_, command)

    def check_service_by_pidfile(self, service, pidfile):
        """Add pidfile to the global checks for service."""
        self.add_pidfile(service, pidfile)
    
    def install_pkg(self, *pkgs):
        """Add packages to the global list of packages to install."""
        for p in pkgs:
            if not p in self.get_pkgs():
                self.add_pkg(p)

    def activate_service(self, name):
        """Add the service to the list of services to be activated."""
        self.add_service((name, True))
        
    def deactivate_service(self, name):
        """Add the service to the list of services to be deactivated."""
        self.add_service((name, False))
        
# plan.py ends here
