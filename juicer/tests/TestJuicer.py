#!/usr/bin/env python
import unittest
from juicer.juicer.Juicer import Juicer as j
from juicer.juicer.Parser import Parser as pmoney
from juicer.admin.JuicerAdmin import JuicerAdmin as ja
from juicer.admin.Parser import Parser as pamoney
from juicer.utils import mute, get_login_info, get_environments
import juicer.common.Constants as Constants
import juicer.common.Cart
import os
import cProfile


PROFILE_LOG = os.getenv('JPROFILELOG', '/tmp/juicer-call-stats')


class TestJuicer(unittest.TestCase):
    def setUp(self):
        self.parser = pmoney()
        self.aparser = pamoney()

        self.cname = 'CHG0DAY'
        self.cpath = os.path.expanduser('%s/%s.json' % (Constants.CART_LOCATION, self.cname))
        self.rname = 'hats'
        (self.connectors, self._defaults) = get_login_info()
        setup_args = self.aparser.parser.parse_args(
            ('repo create %s --in re qa' % self.rname).split())
        pulp_admin = ja(setup_args)
        mute()(pulp_admin.create_repo)(
            repo_name=setup_args.name, envs=setup_args.envs)

    def tearDown(self):
        # aparser = pamoney()

        setup_args = self.aparser.parser.parse_args(
            ('repo delete %s --in re qa' % self.rname).split())
        pulp_admin = ja(setup_args)
        mute()(pulp_admin.delete_repo)(repo_name=setup_args.name, envs=setup_args.envs)

    def test_workflow(self):
        cProfile.runctx('self._test_workflow()', globals(), locals(), PROFILE_LOG)

    def _test_workflow(self):
        rpm_path = '../../share/juicer/empty-0.1-1.noarch.rpm'
        rpm2_path = '../../share/juicer/alsoempty-0.1-1.noarch.rpm'

        if os.path.exists(self.cpath):
            os.remove(self.cpath)

        # test uploading an rpm
        self.args = self.parser.parser.parse_args(
            ('rpm upload -r %s %s' % (self.rname, rpm_path)).split())
        pulp = j(self.args)
        cart = pulp.create('upload-cart', self.args.r)

        self.args = self.parser.parser.parse_args('cart push upload-cart'.split())
        pulp = j(self.args)
        mute()(pulp.push)(cart)

        # test searching for an rpm
        self.args = self.parser.parser.parse_args('rpm search %s'.split())
        pulp = j(self.args)
        mute()(pulp.search)(pkg_name=self.args.rpmname)

        self.args = self.parser.parser.parse_args(
            'rpm search %s --in re'.split())
        pulp = j(self.args)
        mute()(pulp.search)(pkg_name=self.args.rpmname)

        # test creating a cart
        self.args = self.parser.parser.parse_args(('cart create CHG0DAY -r %s %s %s'
                                                   % ('hats', rpm_path, rpm2_path)).split())
        pulp = j(self.args)
        mute()(pulp.create)(cart_name=self.args.cartname, cart_description=self.args.r)

        # test pushing a cart
        self.args = self.parser.parser.parse_args(('cart create %s -r hats %s'
                                                   % (self.cname, rpm_path)).split())
        pulp = j(self.args)
        cart = juicer.common.Cart.Cart(self.args.cartname, autoload=True, autosync=True)
        mute()(pulp.push)(cart=cart)

        # test promoting a cart
        cart = juicer.common.Cart.Cart(self.cname, autoload=True)
        old_env = cart.current_env

        self.args = self.parser.parser.parse_args(('cart promote %s' % self.cname).split())
        pulp = j(self.args)
        mute()(pulp.promote)(cart_name=self.args.cartname)

        cart = juicer.common.Cart.Cart(self.cname, autoload=True)

        self.assertFalse(cart.current_env == old_env)

        # test creating a cart from manifest
        new_cname = 'CHG1DAY'

        self.args = self.parser.parser.parse_args(('cart create %s -f %s' %
                                                   (new_cname, '../../share/juicer/rpm-manifest.yaml')).split())
        pulp = j(self.args)
        mute()(pulp.create_manifest)(cart_name=self.args.cartname, manifests=self.args.f)

        cart = juicer.common.Cart.Cart(new_cname, autoload=True)

        self.assertFalse(cart.is_empty())

        # test deleting a cart
        self.args = self.parser.parser.parse_args(('cart delete %s' % \
                                        (self.cname)).split())
        pulp = j(self.args)

        mute()(pulp.delete)(cartname=cart.cart_name)
        self.assertFalse(os.path.exists(cart.cart_file()))

        cart = juicer.common.Cart.Cart(self.cname, autoload=True)
        mute()(pulp.delete)(cartname=cart.cart_name)
        self.assertFalse(os.path.exists(cart.cart_file()))

    def test_show(self):
        cProfile.runctx('self._test_show()', globals(), locals(), PROFILE_LOG)

    def _test_show(self):
        self.args = self.parser.parser.parse_args(('cart show %s' % self.cname).split())
        pulp = j(self.args)
        mute()(pulp.show)(self.cname, get_environments())

    def test_pull(self):
        cProfile.runctx('self._test_pull()', globals(), locals(), PROFILE_LOG)

    def _test_pull(self):
        if os.path.exists(self.cpath):
            os.remove(self.cpath)

        self.args = self.parser.parser.parse_args(('cart pull %s' % self.cname).split())
        pulp = j(self.args)
        mute()(pulp.pull)(self.cname)

        self.assertTrue(os.path.exists(self.cpath))

    def test_hello(self):
        cProfile.runctx('self._test_hello()', globals(), locals(), PROFILE_LOG)

    def _test_hello(self):
        self.args = self.parser.parser.parse_args(("hello --in %s" % self._defaults['start_in']).split())
        pulp = j(self.args)
        mute()(pulp.hello)()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJuicer)
    unittest.TextTestRunner(verbosity=2).run(suite)
