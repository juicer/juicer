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

## A Non-Trivial Release Workflow

In this example, we have many rpms to be pushed to several different
repositories. We've organized those rpms on our local system into
several folders and possibly have a few stragglers that we've built
using another system.

We'll start by creating this cart `ComplicatedRelease` with items from
two folders and several packages from a build system somewhere on the
Internet:

    $ juicer cart create ComplicatedRelease -r first-repository ~/rpmbuild/juicer* https://remote.buildsystem.host/my-build/my-rpm.0.0.0-1.el6.noarch.rpm \
                                            -r second-repository ~/tmp/pulp/ \
                                            -r third-repository https://remote.buildsystem.host/my-build/my-other-rpm-0.0.0-1.el6.noarch.rpm

Making this cart has created a json cart file on our local system. We
can view the cart by opening the cart file or by running `juicer cart
show` for the system.

    $ juicer cart show ComplicatedRelease

We could also just see the file on the local system and make changes
directly to the json if we wanted to.

    $ cat ~/.config/juicer/carts/ComplicatedRelease.json

We have to push this release to multiple environments. The standard
example environments we use are 're' (release engineering), qa, stage
and prod.

First, we'll push this change to our release engineering
environment. Pulp repositories for this environment are stored in a
`/re/` path on the pulp system.

    $ juicer cart push ComplicatedRelease --in re

We expect this cart to change as rpms get built and updated over
time. We also expect the release engineer responsible for promoting
these rpms to change since our organization operates in many time
zones.

The first release engineer, who promoted the rpms to the `re`
environment must update the cart since more recent package builds have
occurred on the remote system. So she must run a `cart update`:

    $ juicer cart update ComplicatedRelease -r third-repository https://remote.buildsystem.host/my-build/my-other-rpm-0.0.0-2.el6.noarch.rpm

Then she pushes that cart to the release environment once more:

    $ juicer cart push ComplicatedRelease --in re

Now, the release engineer changes. The second release engineer working
in another time zone must push the cart to the `qa` environment. He
doesn't have the cart on his system so he needs to pull the cart down.

    $ juicer cart pull ComplicatedRelease

Then he can push the cart to `qa`.

    $ juicer cart push ComplicatedRelease --in qa

The qa team in that geo is satisfied with the changes and asked the
release engineer to promote the packages to `stage`.

    $ juicer cart push ComplicatedRelease --in stage

At this point in the release, the qa team finds a horrible bug that
must be patched (again on a remote system). So he updates the cart
once more.

    $ juicer cart update ComplicatedRelease -r first-repository https://remote.buildsystem.host/my-build/my-rpm-0.0.0-1.el6.noarch.rpm \
                                            -r third-repository https://remote.buildsystem.host/my-build/my-other-rpm-0.0.0-3.el6.noarch.rpm

Now he has to start over, so he pushes the cart into `re`, `qa`, and
`stage`.

    $ juicer cart push ComplicatedRelease --in re
    $ juicer cart push ComplicatedRelease --in qa
    $ juicer cart push ComplicatedRelease --in stage

Finally the qa team is satisfied, so he pushes the cart to production.

    $ juicer cart push ComplicatedRelease --in prod
