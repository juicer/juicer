# Importing/Exporting Repositories

## Introduction

The `juicer-admin` command provides functionality enabling the
**import** and **export** of repositories. These sub-commands accept
json files as input and return json as output, respectively.

* See also: [Repository Definition Syntax](https://github.com/juicer/juicer/blob/master/docs/markdown/repo_syntax.md)


## Why import/export?

The purpose of these commands is to enable and facilitate data-driven
infrastructures. With **import** you may automatically create/update
all of your repositories. This fits in well with version controlled
configuration management systems.

With **export** you can create a repository definition file describing
all of your existing repositories. (Of course, you didn't create them
all by hand, did you?) The produced file is compliant with what
`juicer-admin repo import` accepts as input.


# Exporting

Here is how to export your current repositories:

    $ juicer-admin repo export --out all_my_repos.json

You may limit the export to a specific environment as well via the
`--in` option:

    $ juicer-admin repo export --out all_my_repos.json --in prod

This sub-command runs in several threads if multiple CPUs are
available. This greatly reduces the time required to compile the repo
definition file for users with several dozens or hundreds of
repositories.

# Importing

Importing can be used to both create new repositories, as well as
update existing repositories. If a repositoriy exists in pulp, but not
in your definition file, then it will be ignored. Repository importing
will **never** delete existing repositories.

Follow the instructions in
[Repository Definition Syntax](https://github.com/juicer/juicer/blob/master/docs/markdown/repo_syntax.md)
and craft a repo def file. Or, follow the previous instructions
(above) for exporting your current repository configurations.

Make any additions or modifications you wish. Upon import, you will be
notified if your json file is improperly formatted. Check out
[JSONLint](http://jsonlint.com/) if you need assistance.

It is advised that you run the **import** in **noop** (or "*dry-run*")
mode first. This will only show you what would have been
created/changed. Stated differently, **noop** mode never makes any
actual changes, it only prints what *would* have happened.

For example:

    $ juicer-admin repo import --noop all_my_repos.json

*Special note*: The *import* sub-command is not restricted by the
 `--in` option.

When you're satisfied with the changes, remove the `--noop` option:

    $ juicer-admin repo import all_my_repos.json
