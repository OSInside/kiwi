#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup
from distutils.command import build
from distutils.command import install
#from distutils.command import install_scripts
import distutils
import subprocess

from kiwi.version import __version__


class kiwi_build(build.build):
    """
    Custom build command
    """
    build.build.user_options += [
        ('cflags=', None, 'compile flags')
    ]

    def initialize_options(self):
        """
        Set default values for options
        Each user option must be listed here with their default value.
        """
        build.build.initialize_options(self)
        self.cflags = ''

    def run(self):
        """
        Run first the related KIWI C compilation and after that
        the usual Python build
        """
        # kiwi C tools compilation
        command = ['make']
        if self.cflags:
            command.append('CFLAGS=%s' % self.cflags)
        command.append('tools')
        self.announce(
            'Running make tools target: %s' % str(command),
            level=distutils.log.INFO
        )
        self.announce(
            subprocess.check_output(command).decode(),
            level=distutils.log.INFO
        )

        # standard build process
        build.build.run(self)


class kiwi_install(install.install):
    """
    Custom install command
    """
    sub_commands = [
        ('install_lib', lambda self:True),
        ('install_headers', lambda self:False),
        ('install_scripts', lambda self:True),
        ('install_data', lambda self:False),
        ('install_egg_info', lambda self:True),
    ]

    def run(self):
        """
        Run first the related KIWI installation tasks and after
        that the usual Python installation
        """
        # kiwi tools, completion and manual pages
        command = ['make']
        if self.root:
            command.append('buildroot=%s/' % self.root)
        command.append('install')
        self.announce(
            'Running make install target: %s' % str(command),
            level=distutils.log.INFO
        )
        self.announce(
            subprocess.check_output(command).decode(),
            level=distutils.log.INFO
        )

        # standard installation
        install.install.run(self)


config = {
    'name': 'kiwi',
    'description': 'KIWI - Appliance Builder',
    'author': 'Marcus Schäfer',
    'url': 'https://github.com/openSUSE/kiwi',
    'download_url': 'https://github.com/openSUSE/kiwi',
    'author_email': 'ms@suse.com',
    'version': __version__,
    'install_requires': [
        'docopt>=0.6.2',
        'lxml',
        'xattr'
    ],
    'packages': ['kiwi'],
    'cmdclass': {
        'build': kiwi_build,
        'install': kiwi_install
    },
    'entry_points': {
        'console_scripts': [
            'kiwi-ng=kiwi.kiwi:main',
            'kiwicompat=kiwi.kiwi_compat:main'
        ]
    },
    'include_package_data': True,
    'zip_safe': False,
    'classifiers': [
       # complete classifier list:
       # http://pypi.python.org/pypi?%3Aaction=list_classifiers
       #'Development Status :: 3 - Alpha',
       #'Development Status :: 4 - Beta',
       #'Development Status :: 5 - Production/Stable',
       'Development Status :: 4 - Beta',
       'Intended Audience :: Developers',
       'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
       'Operating System :: POSIX :: Linux',
       'Programming Language :: Python :: 3.4',
       'Programming Language :: Python :: 3.5',
       'Topic :: System :: Operating System',
    ]
}

setup(**config)
