# Install

## From Source

You'll need these dependencies to run Juicer:

1. python-BeautifulSoup
2. python-requests >= 0.13.1
3. rpm-python
4. python-progressbar
5. python >= 2.5
6. python-yaml
7. pymongo

When the dependencies are satisfied, rename setup.py.in to setup.py:

    $ sudo make install

## Building RPMs From Source

We recommend that you install via RPM if you're pulling down the
Juicer source:

    $ sudo make rpminstall
