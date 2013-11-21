# Hacking

Starting to hack on `juicer` from source is super easy!

## Clone the Source

    $ git clone git://github.com/juicer/juicer.git

## Install Dependencies

See [install](install.md) for a list of dependencies.

## Setup a Config File

See [Config File Setup](config.md) to create a config file
`~/.config/juicer/config`.

## Start Hacking

To set up your `PYTHONPATH`, `PATH`, and `MANPATH` simply run the following:

    $ cd juicer
    $ . ./hacking/setup-env

## Test Your Connections

After you've created a config file and exported your paths you can
test your connections out by running:

    $ juicer hello

## Rebuiding Man Pages

To rebuild the man pages there is an additional dependency:

* `asciidoc`

When satisfied, run:

    $ make docs
