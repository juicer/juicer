from juicer.admin.JuicerAdmin import JuicerAdmin as ja

def create_repo(args):
    pulp = ja(args)
    print pulp.create_repo()

def create_user(args):
    pulp = ja(args)
    print pulp.create_user()

def list_repos(args):
    pulp = ja(args)
    print pulp.list_repos()

def show_repo(args):
    pulp = ja(args)
    print pulp.show_repo()

def show_user(args):
    pulp = ja(args)
    print pulp.show_user()

def delete_repo(args):
    pulp = ja(args)
    print pulp.delete_repo()

def delete_user(args):
    pulp = ja(args)
    print pulp.delete_user()
