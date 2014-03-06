# -*- coding: utf-8 -*-
# Juicer - Administer Pulp and Release Carts
# Copyright © 2012-2014, Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import juicer.utils.Log
from juicer.common.Errors import *
import juicer.common.Cart
from juicer.juicer.Juicer import Juicer as j


def create(args):
    pulp = j(args)
    juicer.utils.Log.log_info("Creating cart '%s'." % args.cartname)

    if args.f:
        juicer.utils.Log.log_debug("Manifest detected.")

        pulp.create_manifest(args.cartname, args.f)
    elif args.r:
        pulp.create(args.cartname, args.r)
    else:
        raise JuicerError("Argument Error")


def update(args):
    pulp = j(args)

    if not args.r and not args.f:
        raise JuicerError("Argument Error")

    cart = pulp.update(args.cartname, args.r, args.f)

    juicer.utils.Log.log_info("Updated cart '%s'." % cart.cart_name)


def edit():
    pass


def show(args):
    pulp = j(args)
    cart = pulp.show(args.cartname, args.environment)
    print cart


def list(args):
    pulp = j(args)
    for cart in pulp.list(args.cart_glob):
        print cart


def pull(args):
    pulp = j(args)
    pulp.pull(args.cartname)


def createlike():
    pass


def push(args):
    pulp = j(args)
    for env in args.environment:
        cart = juicer.common.Cart.Cart(args.cartname, autoload=True, autosync=True)
        pulp.push(cart, env)


def delete_rpm(args):
    pulp = j(args)
    for env in args.environment:
        for repo in args.r:
            repo_name = "%s-%s" % (repo[0], env)
            rpms = repo[1:len(repo)]
            pulp.delete_rpms(repo_name, rpms, env)


def search(args):
    pulp = j(args)
    pulp.search(pkg_name=args.rpmname, search_carts=args.carts)


def upload(args):
    pulp = j(args)

    cart = pulp.create("upload-cart", args.r)
    cart.sync_remotes()

    for env in args.environment:
        pulp.push(cart, env)


def hello(args):
    pulp = j(args)
    pulp.hello()


def promote(args):
    pulp = j(args)
    pulp.promote(cart_name=args.cartname)


def merge(args):
    pulp = j(args)
    pulp.merge(carts=args.carts, new_cart_namename=args.new_cart_name)


def publish(args):
    pulp = j(args)
    for env in args.environment:
        pulp.publish_repo(args.repo, env)


def delete(args):
    pulp = j(args)
    pulp.delete(cartname=args.cartname)
