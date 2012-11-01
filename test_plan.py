#---------------------------------------------------------------
# Project         : adminkit
# File            : test_plan.py
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
# Created On      : Tue Oct 30 22:33:24 2012
# Purpose         : test plan module
#---------------------------------------------------------------

import unittest

import plan

class TestPlanTest(unittest.TestCase):

    def setUp(self):
        self.p = plan.Plan()
        self.p.add_var('hostname', 'host')

    def test_domain(self):
        self.p.define_domain('domain')
        self.assertEqual('domain', self.p.default_domain())

    def test_plan(self):
        self.assertTrue(self.p)

    def test_get_pkgs(self):
        self.assertEqual([], self.p.get_pkgs())

    def test_add_pkg(self):
        self.p.add_pkg('toto')
        self.p.add_role('role')
        self.assertEqual(['toto',], self.p.get_pkgs())
        self.assertEqual(['toto',], self.p.pkg)

    def test_add_var(self):
        self.p.add_var('var', 'value')
        self.assertEqual(self.p.get_var('var'), 'value')

    def test_add_var_host(self):
        self.p.add_var_host('host', 'var', 'value')
        self.assertEqual(self.p.get_var('var'), 'value')

    def test_add_to_list(self):
        self.p.add_to_list('var', 'value')
        self.assertEqual(self.p.get_var('var'), ['value', ])

    def test_add_to_list_host(self):
        self.p.add_to_list_host('host', 'var', 'value')
        self.assertEqual(self.p.get_var('var'), ['value', ])

    def test_get_var(self):
        self.assertEqual(self.p.get_var('var'), None)

    def test_check_host(self):
        self.assertTrue(self.p.check_host('host'))

    def test_add_roles(self):
        self.p.add_roles('host', 'role1', 'role1', 'role2')
        self.assertEqual(['role1', 'role2'], self.p.get_roles())

    def test_add_files(self):
        self.p.add_files('file1', 'file2')
        self.assertEqual(['file1', 'file2'], self.p.get_files())

    def test_files_for_service(self):
        self.p.files_for_service('serv', 'file1', 'file2')
        self.assertEqual(['file1', 'file2'], self.p.get_files())
        self.assertEqual('serv', self.p.get_service('file1'))
        self.assertEqual('serv', self.p.get_service('file2'))

    def test_add_dirs(self):
        self.p.add_dirs('dir1', 'dir2')
        self.assertEqual(['dir1', 'dir2'], self.p.get_dirs())

    def test_check_perms(self):
        self.p.check_perms('perm1', 'perm2')
        self.assertEqual(['perm1', 'perm2'], self.p.get_perms())

    def test_run_once(self):
        self.p.run_once('cmd')
        self.assertEqual(['cmd', ], self.p.get_onces())
        
    def test_files_to_command(self):
        self.p.files_to_command('cmd', 'file1', 'file2')
        self.assertEqual(2, len(self.p.command))

    def test_check_service_by_pidfile(self):
        self.p.check_service_by_pidfile('serv', 'file1')
        self.assertEqual('file1', self.p.get_pidfile('serv'))

    def test_install_pkg(self):
        self.p.install_pkg('pkg1', 'pkg2', 'pkg2')
        self.assertEqual(['pkg1', 'pkg2'], self.p.get_pkgs())
        
if __name__ == "__main__":
    unittest.main()
                                        
# test_plan.py ends here
