#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup
from setuptools.command import sdist as setuptools_sdist

import distutils
import subprocess

from kiwi.version import __version__


class sdist(setuptools_sdist.sdist):
    """
    Custom sdist command
    Host requirements: git
    """
    def run(self):
        """
        Run first the git commit format update $Format:%H$
        and after that the usual Python sdist
        """
        # git attributes
        command = ['make', 'git_attributes']
        self.announce(
            'Running make git_attributes target: %s' % str(command),
            level=distutils.log.INFO
        )
        self.announce(
            subprocess.check_output(command).decode(),
            level=distutils.log.INFO
        )

        # standard sdist process
        setuptools_sdist.sdist.run(self)

        # cleanup attributes
        command = ['make', 'clean_git_attributes']
        self.announce(
            subprocess.check_output(command).decode(),
            level=distutils.log.INFO
        )


config = {
    'name': 'kiwi',
    'python_requires': '>=3.6',
    'description': 'KIWI - Appliance Builder (next generation)',
    'author': 'Marcus Schaefer',
    'url': 'https://osinside.github.io/kiwi',
    'download_url':
        'https://download.opensuse.org/repositories/'
        'Virtualization:/Appliances:/Builder',
    'author_email': 'ms@suse.com',
    'version': __version__,
    'license' : 'GPLv3+',
    'install_requires': [
        'docopt>=0.6.2',
        'lxml',
        'pyxattr',
        'requests',
        'PyYAML'
    ],
    'packages': ['kiwi'],
    'cmdclass': {
        'sdist': sdist
    },
    'entry_points': {
        'kiwi.tasks': [
            'image_info=kiwi.tasks.image_info',
            'image_resize=kiwi.tasks.image_resize',
            'result_bundle=kiwi.tasks.result_bundle',
            'result_list=kiwi.tasks.result_list',
            'system_build=kiwi.tasks.system_build',
            'system_create=kiwi.tasks.system_create',
            'system_prepare=kiwi.tasks.system_prepare',
            'system_update=kiwi.tasks.system_update'
        ],
        'console_scripts': [
            'kiwi-ng=kiwi.kiwi:main',
            'kiwicompat=kiwi.kiwi_compat:main'
        ]
    },
    'include_package_data': True,
    'zip_safe': False,
    'classifiers': [
       # classifier: http://pypi.python.org/pypi?%3Aaction=list_classifiers
       'Development Status :: 5 - Production/Stable',
       'Intended Audience :: Developers',
       'License :: OSI Approved :: '
       'GNU General Public License v3 or later (GPLv3+)',
       'Operating System :: POSIX :: Linux',
       'Programming Language :: Python :: 3.6',
       'Programming Language :: Python :: 3.7',
       'Topic :: System :: Operating System',
    ]
}

setup(**config)
