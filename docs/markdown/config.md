# Config

## How do I configure Juicer?

Juicer is configured through a `~/.config/juicer/config` file. It's broken into
sections by environment. It may also contain an optional `DEFAULT`
section, from which the defaults for all following sections are
supplied.

The standard flow of this sample infrastructure goes from devel to
prod. Meaning that we upload our packages to devel and test them
accordingly in our development environment before we `promote` them to
prod.

    # ~/.config/juicer/config - In this example config file we maintain two
    # environments: devel and prod.

    [DEFAULT]
    username: tux
    password: 5w33tP@ssw04d
    base_url: https://pulp.devel.int.tux.org/pulp/api
    # 'devel' is the base environment. This means juicer will default
    # to using 'devel' when commands are not specified with an
    # explicit environment(s).
    start_in: devel

    # If an environment requires signatures, specify an
    # rpm_sign_plugin. Here we've included MySweetPlugin, which will
    # serve to sign RPMs for us. See juicer.common.RpmSignPlugin.
    rpm_sign_plugin: juicer.plugins.MySweetPlugin

    # Carts are stored in a mongodb instance somewhere, this is the
    #  hostname of our mongodb server.
    cart_host: mongodb01.util.tux.org

    [devel]
    # Most of our configuration for this environment lives in the
    # DEFAULT section already, but we do need to tell Juicer where
    # this environment promotes to next.
    promotes_to: prod

    [prod]
    # username already defined in DEFAULT.
    password: 5w33t_AdM!n_P@ssw04d

    # Note that this is a different pulp server, so we must specify
    # the base_url once again.
    base_url: https://pulp.prod.int.tux.org/pulp/api

    # We specify that the production environment requires packages to
    # be signed.
    requires_signature: true

See also: `man 5 juicer.conf`
