# Install

## From Source

You'll need these dependencies to build/install:

1. python-BeautifulSoup
2. python-request >= 0.13.1
3. rpm-python
4. python-magic
5. python >= 2.5

Building documentation requires the following deps. If you're building
the RPMs, then these are required otherwise they are optional.

1. asciidoc

## Building RPMs From Source

We recommend that you install via RPM if you're pulling down the
Juicer source:

       make rpm
       sudo yum localinstall /path/to/rpm
