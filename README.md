# Juicer

## What is Juicer?

From a Release Engineering point of view, Juicer is a collection of
tools for administering Pulp [1], a Fedora Hosted Project for managing
yum repositories.

Juicer allows you to remotely manage repositories in multiple
environments such as QA, STAGE, or PROD as well as upload and promote
rpm packages through a Pulp installation.

[1] Pulp  https://fedorahosted.org/pulp/

## How do I configure Juicer?

Juicer is configured through a `~/.juicer.conf` file. It's broken into
sections by environment. It may also contain an optional `DEFAULT`
section, from which the defaults for all following sections are
supplied.


    # ~/.juicer.conf - In this example config file we maintain two
    # environments: devel and prod.

    [DEFAULT]
    username: tux
    password: 5w33tP@ssw04d
    base_url: https://pulp.devel.int.tux.org/pulp/api

    [devel]
    # We don't actually need anything *in* this section because its in
    # the DEFAULT section already.

    [prod]
    # username already defined in DEFAULT
    password: 5w33t_AdM!n_P@ssw04d
    base_url: https://pulp.prod.int.tux.org/pulp/api

See also: `man 5 juicer.conf`
