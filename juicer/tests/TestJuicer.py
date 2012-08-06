#!/usr/bin/env python
import unittest
from juicer.juicer.Juicer import Juicer as j
from juicer.juicer.Parser import Parser as pmoney
from juicer.utils import mute
import juicer.common.Cart
import os


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

    def test_workflow(self):
        cname = 'CRQ0DAY'
        cpath = os.path.expanduser('~/.juicer-carts/%s.json' % cname)
        rpm_path = './share/juicer/empty-0.0.1-1.fc17.x86_64.rpm'

        if os.path.exists(cpath):
            os.remove(cpath)

        # test uploading an rpm
        self.args = self.parser.parser.parse_args(('upload -r %s %s' % ('hats', rpm_path)).split())
        pulp = j(self.args)
        cart = pulp.create('upload-cart', self.args.r)
        
        self.args = self.parser.parser.parse_args('push upload-cart'.split())
        pulp = j(self.args)
        mute()(pulp.push)(cart)

        # test creating a cart
        self.args = self.parser.parser.parse_args(('create CRQ0DAY -r %s %s' \
                % ('hats', rpm_path)).split())
        pulp = j(self.args)
        mute()(pulp.create)(cart_name=self.args.cartname, cart_description=self.args.r)

        # test promoting a cart
        cart = juicer.common.Cart.Cart(cname, autoload=True)
        old_env = cart.current_env

        self.args = self.parser.parser.parse_args(('promote %s' % cname).split())
        pulp = j(self.args)
        mute()(pulp.promote)(name=self.args.cartname)

        cart = juicer.common.Cart.Cart(cname, autoload=True)

        if cart.current_env == old_env:
            raise Exception("%s was in %s before and is in %s now!" % \
                    (cart.name, old_env, cart.current_env))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJuicer)
    unittest.TextTestRunner(verbosity=2).run(suite)
