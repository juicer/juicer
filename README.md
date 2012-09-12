# Juicer

## What is Juicer?

From a Release Engineering point of view, Juicer is a collection of
tools for administering Pulp [1], a Fedora Hosted Project for managing
yum repositories.

Juicer allows you to remotely manage repositories in multiple
environments such as QA, STAGE, or PROD as well as upload and promote
rpm packages through a Pulp installation.

[1] Pulp  https://fedorahosted.org/pulp/

## Setting Up and Contributing

1. [Installation](https://github.com/juicer/juicer/blob/master/docs/markdown/install.md)
2. [Configuration](https://github.com/juicer/juicer/blob/master/docs/markdown/config.md)
3. [Hacking](https://github.com/juicer/juicer/blob/master/docs/markdown/hacking.md)
4. [RpmSignPlugins](https://github.com/juicer/juicer/blob/master/docs/markdown/plugins.md)

## Examples

### Upload an rpm into a repository

    $ juicer upload -r juicy-software ~/Downloads/juicer-0.1.7-1.fc17.noarch.rpm

### Example Workflow

Start by creating a release cart `MyJuicyRelease` with items from the Internet:

    $ juicer create MyJuicyRelease -r juicy-software https://my.sweet.host/pulp/repos/dev/juicy-software/juicer-0.1.7-1.fc17.noarch.rpm

Then push the cart and its contents to pulp:

    $ juicer push MyJuicyRelease

When you're satisfied, promote the cart to the next environment
(perhaps `stage`, or `production`):

    $ juicer promote MyJuicyRelease
