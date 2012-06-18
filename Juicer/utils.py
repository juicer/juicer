import ConfigParser
import os

def get_login_info(args):
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

    if config.has_section('base'):
        cfg = dict(config.items('base'))

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

