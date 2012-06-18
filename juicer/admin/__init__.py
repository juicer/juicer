from juicer.admin import admin as ja

def create(args):
    pulp = ja(args)
    pulp.create_repo()
