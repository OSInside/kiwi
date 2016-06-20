#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup
from distutils.command import build as distutils_build
from distutils.command import install as distutils_install
from setuptools.command import sdist as setuptools_sdist
import distutils
import subprocess
import os

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


class build(distutils_build.build):
    """
    Custom build command
    Host requirements: make, C compiler, glibc
    """
    distutils_build.build.user_options += [
        ('cflags=', None, 'compile flags')
    ]

    def initialize_options(self):
        """
        Set default values for options
        Each user option must be listed here with their default value.
        """
        distutils_build.build.initialize_options(self)
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
        distutils_build.build.run(self)


class install(distutils_install.install):
    """
    Custom install command
    Host requirements: make
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
        distutils_install.install.run(self)


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
        'xattr',
        'future',
        'six'
    ],
    'packages': ['kiwi'],
    'cmdclass': {
        'build': build,
        'install': install,
        'sdist': sdist
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
       # classifier: http://pypi.python.org/pypi?%3Aaction=list_classifiers
       'Development Status :: 5 - Production/Stable',
       'Intended Audience :: Developers',
       'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
       'Operating System :: POSIX :: Linux',
       'Programming Language :: Python :: 2.7',
       'Programming Language :: Python :: 3.4',
       'Programming Language :: Python :: 3.5',
       'Topic :: System :: Operating System',
    ]
}

setup(**config)
