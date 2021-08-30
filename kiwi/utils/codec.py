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
import logging

# project
from kiwi.exceptions import KiwiDecodingError

log = logging.getLogger('kiwi')


class Codec:
    """
    **Performs conversions of literal byte sequences to strings**
    """
    @staticmethod
    def decode(literal: bytes) -> str:
        """
        Decodes the given literal with the default encoding. In
        case of failure attemps to decode using utf-8 charset with
        the 'replace' error strategy.

        :param bytes literal: literal to decode

        :return: decoded str

        :rtype: str
        """
        if literal is None:
            return ''
        try:
            return Codec._wrapped_decode(literal)
        except Exception:
            log.warning("Failed decoding literal. Forcing UTF-8 decoding")
            try:
                return Codec._wrapped_decode(
                    literal, encoding='utf_8', error_handling_schema='replace'
                )
            except Exception:
                raise KiwiDecodingError(
                    'Locale setup is not utf-8 compatible'
                )

    @staticmethod
    def _wrapped_decode(
        literal: bytes, encoding: str = '', error_handling_schema: str = ''
    ) -> str:
        # This decode wrapper is only implemented to facilitate unit testing
        if encoding:
            return literal.decode(
                encoding=encoding, errors=error_handling_schema
            )
        else:
            return literal.decode()
