#!/usr/bin/env python
import unittest
from juicer.admin.JuicerAdmin import JuicerAdmin as ja
from juicer.admin.Parser import Parser as pmoney


class TestJuicerAdmin(unittest.TestCase):

    def setUp(self):
        self.parser = pmoney()

    def create_test_user(self):
        args = 'create-user --login cjesop --password cjesop \
                --name "ColonelJesop"'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        pulp.create_user()

    def delete_test_user(self):
        args = 'delete-user cjesop'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        pulp.delete_user()

    def create_test_repo(self):
        args = 'create-repo test-repo-456'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        pulp.create_repo()

    def delete_test_repo(self):
        args = 'delete-repo test-repo-456'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        pulp.delete_repo()

    def test_show_repo(self):
        self.create_test_repo()
        args = 'show-repo test-repo-456'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        self.assertTrue(len(pulp.show_repo()) > 0)
        self.delete_test_repo()

    def test_delete_repo(self):
        self.create_test_repo()
        args = 'delete-repo test-repo-456'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        self.assertTrue(any('Deleted' in k for k in pulp.delete_repo()))

    def test_list_repos(self):
        self.create_test_repo()
        args = 'list-repos'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        self.assertTrue(len(pulp.list_repos()) > 0)
        self.delete_test_repo()

    def test_create_repo(self):
        args = 'create-repo test-repo-456'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        self.assertTrue(any('Created' in k for k in pulp.create_repo()))
        self.delete_test_repo()

    def test_create_user(self):
        args = 'create-user --login cjesop --password cjesop \
                --name "ColonelJesop"'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        self.assertTrue(any('Success' in k for k in pulp.create_user()))
        self.delete_test_user()

    def test_delete_user(self):
        self.create_test_user()
        args = 'delete-user cjesop'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        self.assertTrue(any('Success' in k for k in pulp.delete_user()))

    def test_show_user(self):
        self.create_test_user()
        args = 'show-user cjesop'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        self.assertTrue(len(pulp.show_user()) > 0)
        self.delete_test_user()

    def test_list_roles(self):
        args = 'list-roles'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        self.assertTrue(len(pulp.list_roles()) > 0)

    def test_role_add(self):
        self.create_test_user()
        args = 'role-add --login cjesop --role super-users'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        self.assertTrue(any('Success' in k for k in pulp.role_add()))
        self.delete_test_user()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJuicerAdmin)
    unittest.TextTestRunner(verbosity=2).run(suite)
