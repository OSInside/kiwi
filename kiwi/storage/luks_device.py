# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
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
import os
import logging
from tempfile import NamedTemporaryFile

# project
from kiwi.command import Command
from kiwi.defaults import Defaults
from kiwi.storage.device_provider import DeviceProvider
from kiwi.storage.mapped_device import MappedDevice

from kiwi.exceptions import (
    KiwiLuksSetupError
)

log = logging.getLogger('kiwi')


class LuksDevice(DeviceProvider):
    """
    **Implements luks setup on a storage device**

    :param object storage_provider: Instance of class based on DeviceProvider
    """
    def __init__(self, storage_provider):
        # bind the underlaying block device providing class instance
        # to this object (e.g loop) if present. This is done to guarantee
        # the correct destructor order when the device should be released.
        self.storage_provider = storage_provider

        self.luks_device = None
        self.luks_keyfile = None
        self.luks_name = 'luksRoot'

        self.option_map = {
            'sle12': [
                '--cipher', 'aes-xts-plain64',
                '--key-size', '256',
                '--hash', 'sha1'
            ]
        }

    def get_device(self):
        """
        Instance of MappedDevice providing the luks device

        :return: mapped luks device

        :rtype: MappedDevice
        """
        if self.luks_device:
            return MappedDevice(
                device=self.luks_device, device_provider=self
            )

    def create_crypto_luks(
        self, passphrase, os=None, options=None, keyfile=None
    ):
        """
        Create luks device. Please note the passphrase is readable
        at creation time of this image. Make sure your host system
        is secure while this process runs

        :param string passphrase: credentials
        :param string os:
            distribution name to match distribution specific
            options for cryptsetup
        :param list options: further cryptsetup options
        :param string keyfile: file path name
            file path name which contains an alternative key
            to unlock the luks device
        """
        if not options:
            options = []
        if not passphrase:
            raise KiwiLuksSetupError(
                'passphrase must not be empty'
            )
        if os:
            if os in self.option_map:
                options += self.option_map[os]
            else:
                raise KiwiLuksSetupError(
                    'no custom option configuration found for OS %s' % os
                )
        storage_device = self.storage_provider.get_device()
        log.info('Creating crypto LUKS on %s', storage_device)
        log.info('--> Randomizing...')
        storage_size_mbytes = self.storage_provider.get_byte_size(
            storage_device
        ) / 1048576
        Command.run(
            [
                'dd', 'if=/dev/urandom', 'bs=1M',
                'count=%d' % storage_size_mbytes,
                'of=%s' % storage_device
            ]
        )
        log.info('--> Creating LUKS map')
        passphrase_file = NamedTemporaryFile()
        with open(passphrase_file.name, 'w') as credentials:
            credentials.write(passphrase)
        Command.run(
            [
                'cryptsetup', '-q', '--key-file', passphrase_file.name
            ] + options + [
                'luksFormat', storage_device
            ]
        )
        if keyfile:
            self.luks_keyfile = keyfile
            LuksDevice.create_random_keyfile(keyfile)
            Command.run(
                [
                    'cryptsetup', '--key-file', passphrase_file.name,
                    'luksAddKey', storage_device, keyfile
                ]
            )
        Command.run(
            [
                'cryptsetup', '--key-file', passphrase_file.name,
                'luksOpen', storage_device, self.luks_name
            ]
        )
        self.luks_device = '/dev/mapper/' + self.luks_name

    def create_crypttab(self, filename):
        """
        Create crypttab, setting the UUID of the storage device

        :param string filename: file path name
        """
        storage_device = self.storage_provider.get_device()
        with open(filename, 'w') as crypttab:
            luks_uuid = self.storage_provider.get_uuid(storage_device)
            if self.luks_keyfile:
                crypttab.write(
                    'luks UUID={0} /{1}{2}'.format(
                        luks_uuid, os.path.basename(self.luks_keyfile),
                        os.linesep
                    )
                )
            else:
                crypttab.write(
                    'luks UUID={0}{1}'.format(
                        luks_uuid, os.linesep
                    )
                )

    def is_loop(self):
        """
        Check if storage provider is loop based

        Return loop status from base storage provider

        :return: True or False

        :rtype: bool
        """
        return self.storage_provider.is_loop()

    @staticmethod
    def create_random_keyfile(filename):
        """
        Create keyfile with random data

        :param string filename: file path name
        """
        with open(filename, 'wb') as keyfile:
            keyfile.write(os.urandom(Defaults.get_luks_key_length()))

    def __del__(self):
        if self.luks_device:
            log.info('Cleaning up %s instance', type(self).__name__)
            try:
                Command.run(
                    ['cryptsetup', 'luksClose', self.luks_name]
                )
            except Exception:
                log.warning(
                    'Shutdown of luks map %s failed, %s still busy',
                    self.luks_name, self.luks_device
                )
