from juicer.admin.JuicerAdmin import JuicerAdmin as ja

def create(args):
    pulp = ja(args)
    pulp.create_repo()

def show(args):
    pulp = ja(args)
    pulp.show_repo()

def delete(args):
    pulp = ja(args)
    pulp.delete_repo()
