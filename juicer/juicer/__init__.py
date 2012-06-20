from juicer.juicer.Juicer import Juicer as j
from pprint import pprint as pp

def create():
    pass
def edit():
    pass
def show():
    pass
def update():
    pass
def createlike():
    pass
def publish():
    pass

def cartsearch(args):
    pass

def rpmsearch(args):
    pulp = j(args)
    pp(pulp.search_rpm(name=args.rpmname, envs=args.environment))
