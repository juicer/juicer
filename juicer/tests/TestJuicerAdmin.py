#!/usr/bin/env python
import unittest
from juicer.admin.JuicerAdmin import JuicerAdmin as ja
from juicer.admin.Parser import Parser as pmoney
from juicer.utils import mute, get_login_info, get_environments
import juicer.common.Repo
import cProfile
import os


PROFILE_LOG = os.getenv('JPROFILELOG', '/tmp/juicer-admin-call-stats')


class TestJuicerAdmin(unittest.TestCase):
    def __init(self):
        (self.connectors, self._defaults) = get_login_info()
        for env in get_environments():
            # remove user
            users = self.connectors[env].get('/users/')
            for user in users:
                if user['login'] == 'cjesop':
                    self.connectors[env].delete('/users/%s/' % user['id'])
                    # remove repo
                    self.connectors[env].delete('/repositories/test-repo-456/')

        super(TestJuicerAdmin, self).__init__()

    def setUp(self):
        self.parser = pmoney()
        (self.connectors, self._defaults) = get_login_info()

    def create_test_user(self):
        args = self.parser.parser.parse_args(("user create cjesop --password cjesop --name 'ColonelJesop' --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        mute()(pulp.create_user)(login=args.login, user_name=args.name, password=args.password, \
                                 envs=args.envs)

    def delete_test_user(self):
        args = self.parser.parser.parse_args(("user delete cjesop --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        mute()(pulp.delete_user)(login=args.login, envs=args.envs)

    def create_test_repo(self):
        args = self.parser.parser.parse_args(("repo create test-repo-456 --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        mute()(pulp.create_repo)(repo_name=args.name, envs=args.envs)

    def delete_test_repo(self):
        args = self.parser.parser.parse_args(("repo delete test-repo-456 --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        mute()(pulp.delete_repo)(repo_name=args.name, envs=args.envs)

    def test_show_repo(self):
        cProfile.runctx('self._test_show_repo()', globals(), locals(), PROFILE_LOG)

    def _test_show_repo(self):
        self.create_test_repo()
        env = self._defaults['start_in']
        args = self.parser.parser.parse_args(("repo show test-repo-456  --in %s" % env).split())
        pulp = ja(args)
        output = mute()(pulp.show_repo)(repo_names=args.name, envs=args.envs)
        env_output = output[env][0]
        self.assertEqual('test-repo-456', env_output['name'], msg="Expected to see test-repo-456 in %s" %
                         juicer.utils.create_json_str(env_output, indent=4, cls=juicer.common.Repo.RepoEncoder))
        self.delete_test_repo()

    def test_delete_repo(self):
        cProfile.runctx('self._test_delete_repo()', globals(), locals(), PROFILE_LOG)

    def _test_delete_repo(self):
        self.create_test_repo()
        args = self.parser.parser.parse_args(("repo delete test-repo-456 --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        output = mute(returns_output=True)(pulp.delete_repo)(repo_name=args.name, envs=args.envs)
        self.assertTrue(any('deleted' in k for k in output))

    def test_list_repos(self):
        cProfile.runctx('self._test_list_repos()', globals(), locals(), PROFILE_LOG)

    def _test_list_repos(self):
        self.create_test_repo()
        env = self._defaults['start_in']
        args = self.parser.parser.parse_args(("repo list --in %s" % env).split())
        pulp = ja(args)
        output = mute()(pulp.list_repos)(envs=args.envs)
        env_output = output[env]
        self.assertTrue('test-repo-456' in env_output, msg="Expected to find test-repo-456 in output: %s" %
                        juicer.utils.create_json_str(output, indent=4, cls=juicer.common.Repo.RepoEncoder))
        self.delete_test_repo()

    def test_create_repo(self):
        cProfile.runctx('self._test_create_repo()', globals(), locals(), PROFILE_LOG)

    def _test_create_repo(self):
        args = self.parser.parser.parse_args(("repo create test-repo-456 --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        output = mute(returns_output=True)(pulp.create_repo)(repo_name=args.name, envs=args.envs)
        self.assertTrue(any('created' in k for k in output), msg="'created' not in output: %s" %
                        juicer.utils.create_json_str(output, indent=4, cls=juicer.common.Repo.RepoEncoder))
        self.delete_test_repo()

    def test_create_user(self):
        cProfile.runctx('self._test_create_user()', globals(), locals(), PROFILE_LOG)

    def _test_create_user(self):
        args = self.parser.parser.parse_args(("user create cjesop --password cjesop --name 'ColonelJesop' --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        output = mute(returns_output=True)(pulp.create_user)(login=args.login, user_name=args.name, \
                                                             password=args.password, envs=args.envs)
        self.assertTrue(any((('created' in k) or ('shares' in k)) for k in output))
        self.delete_test_user()

    def test_delete_user(self):
        cProfile.runctx('self._test_delete_user()', globals(), locals(), PROFILE_LOG)

    def _test_delete_user(self):
        self.create_test_user()
        args = self.parser.parser.parse_args(("user delete cjesop --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        output = mute(returns_output=True)(pulp.delete_user)(login=args.login, envs=args.envs)
        self.assertTrue(any('deleted' in k for k in output))

    def test_show_user(self):
        cProfile.runctx('self._test_show_user()', globals(), locals(), PROFILE_LOG)

    def _test_show_user(self):
        self.create_test_user()
        args = self.parser.parser.parse_args(("user show cjesop --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        output = mute(returns_output=True)(pulp.show_user)(login=args.login, envs=args.envs)
        self.assertTrue(any('cjesop' in k for k in output))
        self.delete_test_user()

    def test_list_roles(self):
        cProfile.runctx('self._test_list_roles()', globals(), locals(), PROFILE_LOG)

    def _test_list_roles(self):
        args = self.parser.parser.parse_args(("role list --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        output = mute(returns_output=True)(pulp.list_roles)(envs=args.envs)
        self.assertTrue(any('super-users' in k for k in output))

    def test_role_add(self):
        cProfile.runctx('self._test_role_add()', globals(), locals(), PROFILE_LOG)

    def _test_role_add(self):
        self.create_test_user()
        args = self.parser.parser.parse_args(("role add --login cjesop \
                --role super-users --in %s" % self._defaults['start_in']).split())
        pulp = ja(args)
        output = mute(returns_output=True)(pulp.role_add)(role=args.role, login=args.login, envs=args.envs)
        self.assertTrue(any('added' in k for k in output))
        self.delete_test_user()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJuicerAdmin)
    unittest.TextTestRunner(verbosity=2).run(suite)
