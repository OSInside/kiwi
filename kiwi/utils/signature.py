# Copyright (c) 2022 Marcus Schäfer.  All rights reserved.
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
# project
from kiwi.runtime_config import RuntimeConfig
from kiwi.utils.temporary import Temporary
from kiwi.command import Command

from kiwi.exceptions import KiwiCredentialsError


class Signature:
    """
    **Create signatures**
    """
    def __init__(self, filepath: str) -> None:
        """
        Construct new Signature object

        :param str filepath: file path name
        """
        self.filepath = filepath

    def sign(self) -> None:
        """
        Create an openssl based signature from the given file name
        and attach it at the end of that filename. This method requires
        access to a private key for signing. The path to the private
        key is read from the kiwi runtime config file from the
        following section:

        credentials:
          - verification_metadata_signing_key_file: /path/to/pkey
        """
        runtime_config = RuntimeConfig()
        signing_key_file = runtime_config.\
            get_credentials_verification_metadata_signing_key_file()
        if not signing_key_file:
            raise KiwiCredentialsError(
                '{0} not configured in runtime config'.format(
                    'verification_metadata_signing_key_file'
                )
            )
        signature_file = Temporary().new_file()
        Command.run(
            [
                'openssl', 'dgst', '-sha256',
                '-sigopt', 'rsa_padding_mode:pss',
                '-sigopt', 'rsa_pss_saltlen:-1',
                '-sigopt', 'rsa_mgf1_md:sha256',
                '-sign', signing_key_file,
                '-out', signature_file.name,
                self.filepath
            ]
        )
        with open(signature_file.name, 'rb') as sig_fd:
            signature = sig_fd.read()
            with open(self.filepath, 'ab') as get_signed:
                get_signed.write(signature)
