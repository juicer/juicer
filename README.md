# Juicer

## What is Juicer?

From a Release Engineering point of view, Juicer is a collection of
tools for administering Pulp [1], a Fedora Hosted Project for managing
yum repositories.

Juicer allows you to remotely manage repositories in multiple
environments such as QA, STAGE, or PROD as well as upload and promote
rpm packages through a Pulp installation.

[1] Pulp  https://fedorahosted.org/pulp/

## Download

We have a [public yum repository](http://tbielawa.fedorapeople.org/juicer/) set up for your convenience! We've even provided a [repo file](https://github.com/juicer/juicer/blob/master/docs/juicer.repo) that you can place in /etc/yum.repos.d/ . From there, run

    $ yum install juicer juicer-admin

and you're set!

## Setting Up and Contributing

1. [Installation](https://github.com/juicer/juicer/blob/master/docs/markdown/install.md)
2. [Configuration](https://github.com/juicer/juicer/blob/master/docs/markdown/config.md)
3. [Hacking](https://github.com/juicer/juicer/blob/master/docs/markdown/hacking.md)
4. [RpmSignPlugins](https://github.com/juicer/juicer/blob/master/docs/markdown/plugins.md)
5. [Repo Import/Exporting](https://github.com/juicer/juicer/blob/master/docs/markdown/import_export.md)


## Examples

### Prepare Pulp for use with Juicer

We assume that you have Pulp running already. Pulp ships with a default user whose name and password are both admin. If you've changed that, it's fine. If not, Juicer provides an easy way to do so! Either way, put your account credentials in your juicer.conf. There's really only two things left to configure Pulp for use with Juicer.

First, you need to decide on how many Pulp environments you're going to have. At least three (dev, qa, and prod) is recommended. Then, configure Juicer to use them.

    $ man juicer.conf


Now you're ready to start creating release carts!

### Upload an rpm into a repository

    $ juicer rpm upload -r juicy-software ~/Downloads/juicer-0.1.7-1.fc17.noarch.rpm

### Example Workflow

Start by creating a release cart `MyJuicyRelease` with items from the Internet:

    $ juicer cart create MyJuicyRelease -r juicy-software https://my.sweet.host/pulp/repos/dev/juicy-software/juicer-0.1.7-1.fc17.noarch.rpm

Then push the cart and its contents to pulp:

    $ juicer cart push MyJuicyRelease

When you're satisfied, promote the cart to the next environment
(perhaps `stage`, or `production`):

    $ juicer cart promote MyJuicyRelease
