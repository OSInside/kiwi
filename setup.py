#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup
from kiwi.version import __version__

config = {
    'name': 'kiwi',
    'description': 'KIWI - Appliance Builder',
    'author': 'Marcus Schäfer',
    'url': 'https://github.com/openSUSE/kiwi',
    'download_url': 'https://github.com/openSUSE/kiwi',
    'author_email': 'ms@suse.com',
    'version': __version__,
    'install_requires': [
        'docopt==0.6.2',
        'lxml'
    ],
    'packages': ['kiwi'],
    'entry_points': {
        'console_scripts': ['kiwi=kiwi.kiwi:main'],
    },

    'include_package_data': True,
    'zip_safe': False,
    'classifiers': [
       # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
       #'Development Status :: 3 - Alpha',
       #'Development Status :: 4 - Beta',
       #'Development Status :: 5 - Production/Stable',
       'Development Status :: 4 - Beta',
       'Intended Audience :: Developers',
       'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
       'Operating System :: POSIX :: Linux',
       'Programming Language :: Python :: 2.7',
       'Programming Language :: Python :: 3.3',
       'Topic :: System :: Operating System',
    ],
}

setup(**config)
