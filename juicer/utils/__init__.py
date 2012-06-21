# -*- coding: utf-8 -*-
import ConfigParser
import juicer.common
import os

def get_login_info(args, env):
    """
    Give back a dict with the default connection information
    """
    config = ConfigParser.RawConfigParser()
    config_file = os.path.expanduser('~/.juicer.conf')
    required_keys = set(['username', 'password', 'base_url'])

    if os.path.exists(config_file) and os.access(config_file, os.R_OK):
        config.read(config_file)
    else:
        raise IOError("Can not read %s" % config_file)

    if config.has_section(env):
        cfg = dict(config.items(env))

        if args.v > 1:
            print "Configuration information:"
            print cfg

        if not required_keys == set(cfg.keys()):
            raise Exception("Missing values in config file: %s" % \
                                ", ".join(list(required_keys - set(cfg.keys()))))

        return cfg
    else:
        raise Exception("Unable to locate config block for base settings' in '%s'" % \
                            (env, config_file))

def user_exists_p(args, base_url, connector):
    """
    Determine if user exists in specified environment
    """
    url = base_url + '/users/' + args.login + '/'
    _r = connector.get(url)
    print _r.status_code
    return (_r.status_code == 200)

