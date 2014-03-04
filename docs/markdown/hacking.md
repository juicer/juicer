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


## Enabling Code Profiling

If you want to generate stats databases usable by the python `Stats`
class there are two environment variables you can set:

* `JPROFILE` - **required** - Profiling is enabled if this is set to **any** value
* `JPROFILELOG` - **optional** - The default locations are
  `/tmp/juicer-call-stats` and `/tmp/juicer-admin-call-stats`

Here's an example of how to enable profiling with a custom stats db path:

    $ JPROFILE=y JPROFILELOG=/tmp/j.foo juicer-admin repo import --noop ./repo_def_example.json
    [PROFILING ENABLED] Log will be written to /tmp/j.foo

This will enable code profiling because `JPROFILE=y` is set. The stats
db will be saved to `/tmp/j.foo`.

    $ JPROFILE=y juicer-admin repo import --noop ./repo_def_example.json
    [PROFILING ENABLED] Log will be written to /tmp/juicer-admin-call-stats

Likewise, profiling is now enabled. The stats db will be saved to the
default location: `/tmp/juicer-admin-call-stats`.

**Note:** The `[PROFILING ENABLED]` message is written to `stderr`, so
it won't interfere with your pipeline.


## Rebuiding Man Pages

To rebuild the man pages there is an additional dependency:

* `asciidoc`

When satisfied, run:

    $ make docs
