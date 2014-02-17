# Repo File Syntax

## Introduction

Repositories can be automatically created from a **json** document which
follows a specific syntax. This document describes that syntax.

The overall structure of the json document reads like this:

- The base datastructure of the document is a list
- Each item in the list is a repository definition (repo def)
- Each repo def is a hash, or dictionary
- Each hash MUST have a `name` key, which is the repository name
- Each hash MAY have zero or more of the following **optional** keys
    - `arch`
    - `checksum_type`
    - `feed`
	- `env`

## Repository Definition Keys

- `name`
    - **Required** - Yes
    - **Description** - The repository name. Must match the regular expression `([a-zA-Z-_.]+)` (alphanumeric characters, `.`, `-`, and `_`)

- `arch`
    - **Description** - The repository package architecture (like `i386`, or `x86_64`)
    - **Required** - No
    - **Default Value** - `noarch`

- `checksum_type`
    - **Description** - The checksum type to use when generating meta-data
    - **Required** - No
    - **Default Value** - `sha256`
    - **Choices:**
        - sha
        - sha256

- `feed`
    - **Description** -  A feed url from which to synchronize yum repository packages
    - **Required** - No
    - **Default Value** - None

- `env`
    - **Description** - A list of environments this repository should exist in
    - **Required** - No
    - **Default Value** - By default repositories are created in all environments

## Example Repository Definition File

Here's a simple repo def with just two repositories defined:
**repo01**, and **repo02**. **repo01** uses all the default values,
while **repo02** sets the `arch` to `x86_64`. These repos would be
created in all environments.

    [
        {
            'name': 'repo01'
        },
        {
            'name': 'repo02',
            'arch': 'x86_64'
        }
    ]

We could have also written it like this:

    [{'name': 'repo01'}, {'name': 'repo02', 'arch': 'x86_64'}]

Or even like this:

    [
        {'name': 'repo01'},
        {'name': 'repo02', 'arch': 'x86_64'}
    ]

Here's an example with another repository definition. It exercises all
of the optional keys, as well as demonstrates some more alternative
syntax:


    [
        {'name': 'repo01', 'env': ['prod']},
        {'name': 'repo02', 'arch': 'x86_64'},
        {
            'name': 'fedora_mirror',
            'feed': 'http://download.fedoraproject.org/pub/fedora/linux/releases/20/Everything/x86_64/os/',
            'arch': 'x86_64',
            'checksum_type': 'sha',
            'env': ['dev', 'prod']
        }
    ]

- **repo01** will only be created in *prod*
- **repo02** sets it's architecture type to *x86_64*, and is created in *all environments*
- **fedora_mirror** syncs content from it's feed of
  *http://download.fedoraproject.org/pub/fedora/linux/releases/20/Everything/x86_64/os/*,
  sets it's arch to *x86_64*, checksum type to *sha*, and only is
  created in the *dev* and *prod* environments

# Protips (Troubleshooting)

- Don't end lists or hashes with trailing commas
- Remember to close all of your braces and brackets: Each `[` has a matching `]`, each `{` has a matching `}`
- Use a `javascript` mode in your editor if it doesn't have a native `json` mode
- Setting `env` to an empty list (`[]`) will **not** delete the repo from any environment
