import os
import sys

from distutils.core import setup

setup(name='juicer',
      version='0',
      description='Administer Pulp and Release Carts',
      author='GCA-PC',
      author_email='it-pc-list@redhat.com',
      url='https://docspace.corp.redhat.com/docs/DOC-104668',
      license='GPLv3+',
      install_requires=['python-requests'],
      package_dir={ 'juicer': 'juicer' },
      packages=[
         'juicer',
         'juicer.juicer',
         'juicer.admin',
         'juicer.common',
      ],
      scripts=[
         'bin/juicer',
         'bin/juicer-admin'
      ]
)
