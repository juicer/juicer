# -*- coding: utf-8 -*-
# Juicer - Administer Pulp and Release Carts
# Copyright © 2012, Red Hat, Inc.
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
import juicer.common.Cart
from juicer.juicer.Juicer import Juicer as j


def create(args):
    pulp = j(args)
    juicer.utils.Log.log_info("Creating cart '%s'." % args.cartname)
    cart = pulp.create(args.cartname, args.r)
    juicer.utils.Log.log_info("Saved cart '%s'." % args.cartname)
    print cart


def edit():
    pass


def show(args):
    pulp = j(args)
    cart = pulp.show(args.cartname)
    print cart


def pull(args):
    pulp = j(args)
    pulp.pull(args.cartname)


def createlike():
    pass


def push(args):
    pulp = j(args)
    cart = juicer.common.Cart.Cart(args.cartname, autoload=True, autosync=True)
    for env in args.environment:
        pulp.push(cart, env)


def cartsearch(args):
    pass


def rpmsearch(args):
    pulp = j(args)
    pulp.search_rpm(name=args.rpmname)


def upload(args):
    pulp = j(args)

    cart = pulp.create("upload-cart", args.r)

    for env in args.environment:
        pulp.push(cart, env)


def hello(args):
    pulp = j(args)
    pulp.hello()


def promote(args):
    pulp = j(args)
    pulp.promote(name=args.cartname)
