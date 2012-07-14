#!/usr/bin/env python
import unittest
from juicer.admin.JuicerAdmin import JuicerAdmin as ja
from juicer.admin.Parser import Parser as pmoney
from juicer.utils import mute


class TestJuicerAdmin(unittest.TestCase):

    def setUp(self):
        self.parser = pmoney()

    def create_test_user(self):
        args = 'create-user --login cjesop --password cjesop \
                --name "ColonelJesop"'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        mute()(pulp.create_user)()

    def delete_test_user(self):
        args = 'delete-user cjesop'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        mute()(pulp.delete_user)()

    def create_test_repo(self):
        args = 'create-repo test-repo-456'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        mute()(pulp.create_repo)()

    def delete_test_repo(self):
        args = 'delete-repo test-repo-456'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        mute()(pulp.delete_repo)()

    def test_show_repo(self):
        self.create_test_repo()
        args = 'show-repo test-repo-456'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        output = mute(True)(pulp.show_repo)()
        self.assertTrue(any('test-repo-456' in k for k in output))
        self.delete_test_repo()

    def test_delete_repo(self):
        self.create_test_repo()
        args = 'delete-repo test-repo-456'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        output = mute(True)(pulp.delete_repo)()
        self.assertTrue(any('deleted' in k for k in output))

    def test_list_repos(self):
        self.create_test_repo()
        args = 'list-repos'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        output = mute(True)(pulp.list_repos)()
        self.assertTrue('test-repo-456' in output)
        self.delete_test_repo()

    def test_create_repo(self):
        args = 'create-repo test-repo-456'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        output = mute(True)(pulp.create_repo)()
        self.assertTrue(any('created' in k for k in output))
        self.delete_test_repo()

    def test_create_user(self):
        args = 'create-user --login cjesop --password cjesop \
                --name "ColonelJesop"'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        output = mute(True)(pulp.create_user)()
        self.assertTrue(any('created' in k for k in output))
        self.delete_test_user()

    def test_delete_user(self):
        self.create_test_user()
        args = 'delete-user cjesop'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        output = mute(True)(pulp.delete_user)()
        self.assertTrue(any('deleted' in k for k in output))

    def test_show_user(self):
        self.create_test_user()
        args = 'show-user cjesop'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        output = mute(True)(pulp.show_user)()
        self.assertTrue(any('cjesop' in k for k in output))
        self.delete_test_user()

    def test_list_roles(self):
        args = 'list-roles'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        output = mute(True)(pulp.list_roles)()
        self.assertTrue(any('super-users' in k for k in output))

    def test_role_add(self):
        self.create_test_user()
        args = 'role-add --login cjesop --role super-users'
        pulp = ja(self.parser.parser.parse_args(args.split()))
        output = mute(True)(pulp.role_add)()
        self.assertTrue(any('added' in k for k in output))
        self.delete_test_user()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJuicerAdmin)
    unittest.TextTestRunner(verbosity=2).run(suite)
