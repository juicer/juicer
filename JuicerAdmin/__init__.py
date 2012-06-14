from JuicerAdmin import JuicerAdmin as ja

def create(args):
    pulp = ja(args)
    pulp.create_repo()
