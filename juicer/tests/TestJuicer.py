#!/usr/bin/env python
import unittest
from juicer.juicer.Juicer import Juicer as j
from juicer.juicer.Parser import Parser as pmoney


class TestJuicer(unittest.TestCase):

    def setUp(self):
        self.parser = pmoney()

    def test_rpm_search(self):
        self.args = self.parser.parser.parse_args('rpm-search ruby'.split())
        pulp = j(self.args)
        print pulp.search_rpm(name=self.args.rpmname, \
                envs=self.args.environment)

        self.args = self.parser.parser.parse_args(\
                'rpm-search ruby --in qa'.split())
        pulp = j(self.args)
        print pulp.search_rpm(name=self.args.rpmname, \
                envs=self.args.environment)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJuicer)
    unittest.TextTestRunner(verbosity=2).run(suite)
