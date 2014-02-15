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

## Repository Definition Keys

- `name`
    - **Required** - Yes
    - **Description** - The repository name. Must match the regular expression `([a-zA-Z-_.]+)` (alphanumeric characters, `.`, `-`, and `_`)

- `arch`
    - **Required** - No
    - **Description** - The repository package architecture (like `i386`, or `x86_64`)
    - **Default Value** - `noarch`

- `checksum_type`
    - **Required** - No
    - **Description** - The checksum type to use when generating meta-data
    - **Default Value** - `sha256`
    - **Choices:**
        - sha
        - sha256

- `feed`
    - **Required** - No
    - **Description** -  A feed url from which to synchronize yum repository packages
    - **Default Value** - None


## Example Repository Definition File

Here's a simple repo def with just two repositories defined:
**repo01**, and **repo02**. **repo01** uses all the default values,
while **repo02** sets the `arch` to `x86_64`.

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
        {'name': 'repo01'},
        {'name': 'repo02', 'arch': 'x86_64'},
        {
            'name': 'fedora_mirror',
            'feed': 'http://download.fedoraproject.org/pub/fedora/linux/releases/20/Everything/x86_64/os/',
            'arch': 'x86_64',
            'checksum_type': 'sha'
        }
    ]

# Protips (Troubleshooting)

- Don't end lists or hashes with trailing commas
- Remember to close all of your braces and brackets: Each `[` has a matching `]`, each `{` has a matching `}`
- Use a `javascript` mode in your editor if it doesn't have a native `json` mode
