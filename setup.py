#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as readme:
    long_description = readme.read()

config = {
    'name': 'kiwi',
    'long_description': long_description,
    'long_description_content_type': 'text/x-rst',
    'license' : 'GPLv3+',
    'packages': [
        'kiwi',
        'kiwi.boot',
        'kiwi.utils',
        'kiwi.container.setup',
        'kiwi.markup',
        'kiwi.archive',
        'kiwi.bootloader',
        'kiwi.boot.image',
        'kiwi.bootloader.template',
        'kiwi.bootloader.install',
        'kiwi.bootloader.config',
        'kiwi.builder',
        'kiwi.container',
        'kiwi.filesystem',
        'kiwi.package_manager',
        'kiwi.partitioner',
        'kiwi.repository',
        'kiwi.repository.template',
        'kiwi.schema',
        'kiwi.storage',
        'kiwi.storage.subformat',
        'kiwi.storage.subformat.template',
        'kiwi.system',
        'kiwi.system.root_import',
        'kiwi.volume_manager',
        'kiwi.xsl',
        'kiwi.schema',
        'kiwi.config',
        'kiwi.tasks',
        'kiwi.solver',
        'kiwi.solver.repository',
        'kiwi.iso_tools',
        'kiwi.oci_tools'
    ],
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
    }
}

setup(**config)
