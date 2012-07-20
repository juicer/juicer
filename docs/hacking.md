# Hacking

Starting to hack on juicer and run juicer or juicer-admin from your
clone is super easy!

## Clone the Source

	git clone git://github.com/abutcher/juicer.git

## Install Dependencies

1. python-BeautifulSoup
2. python-request >= 0.13.1
3. rpm-python
4. python-magic
5. python >= 2.5

## Setup a Config File

See [Config File Setup](config.md) to create a config file
`~/.juicer.conf`.

## Start Hacking

To set up your PYTHONPATH, PATH, and MANPATH simply run the following:

   cd juicer
   . ./hacking/setup-env

## Test Your Connections

After you've created a config file and exported your paths you can
test your connections out by running:

   juicer hello
