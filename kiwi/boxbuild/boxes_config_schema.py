# Copyright (c) 2020 SUSE Software Solutions Germany GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
schema = {
    'box': {
        'required': True,
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'name': {
                    'type': 'string',
                    'required': True,
                    'empty': False
                },
                'mem_mb': {
                    'type': 'string',
                    'required': True,
                    'empty': False
                },
                'processors': {
                    'type': 'number',
                    'required': False,
                    'empty': False
                },
                'console': {
                    'type': 'string',
                    'required': True,
                    'empty': False
                },
                'arch': {
                    'required': True,
                    'type': 'list',
                    'schema': {
                        'type': 'dict',
                        'schema': {
                            'name': {
                                'type': 'string',
                                'allowed':
                                    ['x86_64', 's390x', 'aarch64', 'ppc64', 'ppc64le'],
                                'required': True,
                                'empty': False
                            },
                            'cmdline': {
                                'type': 'list',
                                'required': True,
                                'nullable': False
                            },
                            'source': {
                                'type': 'string',
                                'required': True,
                                'empty': False
                            },
                            'packages_file': {
                                'type': 'string',
                                'required': True,
                                'empty': False
                            },
                            'boxfiles': {
                                'type': 'list',
                                'required': True,
                                'nullable': False
                            },
                            'container': {
                                'type': 'string',
                                'required': True,
                                'nullable': False
                            },
                            'use_initrd': {
                                'type': 'boolean',
                                'required': True
                            }
                        }
                    }
                }
            }
        }
    }
}
