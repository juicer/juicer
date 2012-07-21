#!/usr/bin/env python
import unittest
from juicer.admin.JuicerAdmin import JuicerAdmin as ja
from juicer.admin.Parser import Parser as pmoney
from juicer.utils import mute, get_login_info, get_environments


class TestJuicerAdmin(unittest.TestCase):

    def __init(self):
        try:
            (self.connectors, self._defaults) = get_login_info()
            for env in get_environments():
                # remove user
                users = self.connectors[env].get('/users/')
                for user in users:
                    if user['login'] == 'cjesop':
                        self.connectors[env].delete('/users/%s/' % user['id'])
                # remove repo
                self.connectors[env].delete('/repositories/test-repo-456/')
        except:
            pass

        super(__init__)

    def setUp(self):
        self.parser = pmoney()

    def create_test_user(self):
        args = self.parser.parser.parse_args('create-user cjesop --password cjesop --name "ColonelJesop"'.split())
        pulp = ja(args)
        mute()(pulp.create_user)(login=args.login, name=args.name, password=args.password, \
                                     envs=args.envs)

    def delete_test_user(self):
        args = self.parser.parser.parse_args('delete-user cjesop'.split())
        pulp = ja(args)
        mute()(pulp.delete_user)(login=args.login, envs=args.envs)

    def create_test_repo(self):
        args = self.parser.parser.parse_args('create-repo test-repo-456'.split())
        pulp = ja(args)
        mute()(pulp.create_repo)(arch=args.arch, name=args.name, envs=args.envs)

    def delete_test_repo(self):
        args = self.parser.parser.parse_args('delete-repo test-repo-456'.split())
        pulp = ja(args)
        mute()(pulp.delete_repo)(name=args.name, envs=args.envs)

    def test_show_repo(self):
        self.create_test_repo()
        args = self.parser.parser.parse_args('show-repo test-repo-456'.split())
        pulp = ja(args)
        output = mute(True)(pulp.show_repo)(name=args.name, envs=args.envs)
        self.assertTrue(any('test-repo-456' in k for k in output))
        self.delete_test_repo()

    def test_delete_repo(self):
        self.create_test_repo()
        args = self.parser.parser.parse_args('delete-repo test-repo-456'.split())
        pulp = ja(args)
        output = mute(True)(pulp.delete_repo)(name=args.name, envs=args.envs)
        self.assertTrue(any('deleted' in k for k in output))

    def test_list_repos(self):
        self.create_test_repo()
        args = self.parser.parser.parse_args('list-repos'.split())
        pulp = ja(args)
        output = mute(True)(pulp.list_repos)(envs=args.envs)
        self.assertTrue('test-repo-456' in output)
        self.delete_test_repo()

    def test_create_repo(self):
        args = self.parser.parser.parse_args('create-repo test-repo-456'.split())
        pulp = ja(args)
        output = mute(True)(pulp.create_repo)(arch=args.arch, name=args.name, envs=args.envs)
        self.assertTrue(any('created' in k for k in output))
        self.delete_test_repo()

    def test_create_user(self):
        args = self.parser.parser.parse_args('create-user cjesop --password cjesop --name "ColonelJesop"'.split())
        pulp = ja(args)
        output = mute(True)(pulp.create_user)(login=args.login, name=args.name, \
                                                  password=args.password, envs=args.envs)
        self.assertTrue(any('created' in k for k in output))
        self.delete_test_user()

    def test_delete_user(self):
        self.create_test_user()
        args = self.parser.parser.parse_args('delete-user cjesop'.split())
        pulp = ja(args)
        output = mute(True)(pulp.delete_user)(login=args.login, envs=args.envs)
        self.assertTrue(any('deleted' in k for k in output))

    def test_show_user(self):
        self.create_test_user()
        args = self.parser.parser.parse_args('show-user cjesop'.split())
        pulp = ja(args)
        output = mute(True)(pulp.show_user)(login=args.login, envs=args.envs)
        self.assertTrue(any('cjesop' in k for k in output))
        self.delete_test_user()

    def test_list_roles(self):
        args = self.parser.parser.parse_args('list-roles'.split())
        pulp = ja(args)
        output = mute(True)(pulp.list_roles)(envs=args.envs)
        self.assertTrue(any('super-users' in k for k in output))

    def test_role_add(self):
        self.create_test_user()
        args = self.parser.parser.parse_args('role-add --login cjesop \
                --role super-users'.split())
        pulp = ja(args)
        output = mute(True)(pulp.role_add)(role=args.role, login=args.login, envs=args.envs)
        self.assertTrue(any('added' in k for k in output))
        self.delete_test_user()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJuicerAdmin)
    unittest.TextTestRunner(verbosity=2).run(suite)
