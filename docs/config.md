# Config

## How do I configure Juicer?

Juicer is configured through a `~/.juicer.conf` file. It's broken into
sections by environment. It may also contain an optional `DEFAULT`
section, from which the defaults for all following sections are
supplied.

The standard flow of this sample infrastructure goes from devel to
prod. Meaning that we upload our packages to devel and test them
accordingly in our development environment before we `promote` them to
prod.

    # ~/.juicer.conf - In this example config file we maintain two
    # environments: devel and prod.

    [DEFAULT]
    username: tux
    password: 5w33tP@ssw04d
    base_url: https://pulp.devel.int.tux.org/pulp/api

    [devel]
    # Most of our configuration for this environment lives the DEFAULT
    # section already but we do need to tell Juicer where we promote
    # to from devel and also that devel is the base environment.
    promotes_to: prod
    base

    [prod]
    # username already defined in DEFAULT
    password: 5w33t_AdM!n_P@ssw04d
    base_url: https://pulp.prod.int.tux.org/pulp/api
    promotes_to: False
    requires_signature

See also: `man 5 juicer.conf`
