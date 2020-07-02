#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup
from setuptools.command import sdist as setuptools_sdist

from distutils.command import build as distutils_build
from distutils.command import install as distutils_install
from distutils.command import clean as distutils_clean

import distutils
import subprocess
import os
import sys

import platform

from kiwi.version import __version__


python_version = platform.python_version().split('.')[0]

# sys.base_prefix points to the installation prefix set during python
# compilation and sys.prefix points to the same path unless we are inside
# a venv, in which case points to the $VIRTUAL_ENV value.
is_venv = sys.base_prefix != sys.prefix if sys.version_info >= (3, 3) else False


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
        command.append('python_version={0}'.format(python_version))
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


class clean(distutils_clean.clean):
    """
    Custom clean command to remove temporary files after `setup.py sdist` or
    `setup.py develop`
    """
    def initialize_options(self):
        distutils_clean.clean.initialize_options(self)
        self.clean_directories = [
            '{0}.egg-info'.format(self.distribution.get_name()), 'dist'
        ]

    def finalize_options(self):
        distutils_clean.clean.finalize_options(self)

    def run(self):
        for directory in self.clean_directories:
            if os.path.exists(directory):
                distutils.dir_util.remove_tree(directory, dry_run=self.dry_run)

        # standard cleaning
        distutils_clean.clean.run(self)


class install(distutils_install.install):
    """
    Custom install command
    Host requirements: make
    """
    distutils_install.install.user_options += [
        ('single-version-externally-managed', None,
         "used by system package builders to create 'flat' eggs")
    ]

    sub_commands = [
        ('install_lib', lambda self:True),
        ('install_headers', lambda self:False),
        ('install_scripts', lambda self:True),
        ('install_data', lambda self:False),
        ('install_egg_info', lambda self:True),
    ]

    def initialize_options(self):
        """
        Set default values for options
        Each user option must be listed here with their default value.
        """
        distutils_install.install.initialize_options(self)
        self.single_version_externally_managed = None

    def run(self):
        """
        Run first the related KIWI installation tasks and after
        that the usual Python installation
        """
        # kiwi tools, completion and manual pages
        command = ['make']
        if self.root:
            command.append('buildroot={0}/'.format(self.root))
        elif is_venv:
            command.append('buildroot={0}/'.format(sys.prefix))
        command.append('python_version={0}'.format(python_version))
        command.append('tools')
        command.append('install')
        self.announce(
            'Running make tools, install targets: %s' % str(command),
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
        'build': build,
        'install': install,
        'sdist': sdist,
        'clean': clean
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
