#!/usr/bin/env python
import unittest
from juicer.admin.JuicerAdmin import JuicerAdmin as ja
from juicer.admin.Parser import Parser as pmoney

class TestJuicerAdmin(unittest.TestCase):
    
    def setUp(self):
        self.parser = pmoney()
    
    def test_repo(self):
        self.args = self.parser.parser.parse_args('create-repo test-repo-456'.split())
        pulp = ja(self.args)
        print pulp.create_repo()
        self.args = self.parser.parser.parse_args('show-repo test-repo-456'.split())
        pulp = ja(self.args)
        print pulp.show_repo()
        self.args = self.parser.parser.parse_args('list-repos'.split())
        pulp = ja(self.args)
        print pulp.list_repos()
        self.args = self.parser.parser.parse_args('delete-repo test-repo-456'.split())
        pulp = ja(self.args)
        print pulp.delete_repo()

    def test_user(self):
        self.args = self.parser.parser.parse_args('create-user --login cjesop --password cjesop --name "ColonelJesop"'.split())
        pulp = ja(self.args)
        print pulp.create_user()
        self.args = self.parser.parser.parse_args('show-user cjesop'.split())
        pulp = ja(self.args)
        print pulp.show_user()
        self.args = self.parser.parser.parse_args('role-add --login cjesop --role super-users'.split())
        pulp = ja(self.args)
        print pulp.role_add()
        self.args = self.parser.parser.parse_args('delete-user cjesop'.split())
        pulp = ja(self.args)
        print pulp.delete_user()

    def test_list_roles(self):
        self.args = self.parser.parser.parse_args('list-roles'.split())
        pulp = ja(self.args)
        print pulp.list_roles()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJuicerAdmin)
    unittest.TextTestRunner(verbosity=2).run(suite)
