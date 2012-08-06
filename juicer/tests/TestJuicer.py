#!/usr/bin/env python
import unittest
from juicer.juicer.Juicer import Juicer as j
from juicer.juicer.Parser import Parser as pmoney
from juicer.utils import mute


class TestJuicer(unittest.TestCase):

    def setUp(self):
        self.parser = pmoney()

    def test_rpm_search(self):
        self.args = self.parser.parser.parse_args('rpm-search ruby'.split())
        pulp = j(self.args)
        mute()(pulp.search_rpm)(name=self.args.rpmname)

        self.args = self.parser.parser.parse_args(\
            'rpm-search ruby --in qa'.split())
        pulp = j(self.args)
        mute()(pulp.search_rpm)(name=self.args.rpmname)

    def test_create(self):
        rpm_path = './share/juicer/empty-0.0.1-1.fc17.x86_64.rpm'
        self.args = self.parser.parser.parse_args(('create CRQ0DAY -r %s %s' % ('hats', rpm_path)).split())
        pulp = j(self.args)
        mute()(pulp.create)(cart_name=self.args.cartname, cart_description=self.args.r)

    def test_promotion(self):
        self.args = self.parser.parser.parse_args('promote CRQ0DAY'.split())
        pulp = j(self.args)
        mute()(pulp.promote)(name=self.args.cartname)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJuicer)
    unittest.TextTestRunner(verbosity=2).run(suite)
