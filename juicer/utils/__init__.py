# -*- coding: utf-8 -*-
import ConfigParser
import juicer.common
import os

def get_login_info():
    """
    Give back an array of dicts with the connection
    information for all the environments
    """
    config = ConfigParser.SafeConfigParser()
    config_file = os.path.expanduser('~/.juicer.conf')
    required_keys = set(['username', 'password', 'base_url'])
    connections = {}

    if os.path.exists(config_file) and os.access(config_file, os.R_OK):
        config.read(config_file)
    else:
        raise IOError("Can not read %s" % config_file)

    for section in config.sections():
        cfg = dict(config.items(section))

        if not required_keys == set(cfg.keys()):
            raise Exception("Missing values in config file: %s" % \
                                ", ".join(list(required_keys - set(cfg.keys()))))

        connections[section] = juicer.common.JuicerCommon(cfg)

    return connections

def user_exists_p(args, connector):
    """
    Determine if user exists in specified environment
    """
    url = '/users/' + args.login + '/'
    _r = connector.get(url)
    return (_r.status_code == 200)

def role_exists_p(args, connector):
    url = connector.base_url + '/roles/' + args.role + '/'
    _r = connector.get(url)
    return (_r.status_code == 200)
