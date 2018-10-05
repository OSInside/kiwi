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

from kiwi.logger import log
from kiwi.exceptions import KiwiDecodingError


class Codec(object):
    """
    **Performs conversions of literal byte sequences to strings**
    """
    @classmethod
    def decode(self, literal):
        """
        Decodes the given literal with the default charset. In case of
        failure attemps to decode using utf-8 charset.

        :param bytes literal: literal to decode

        :return: decoded string
        :rtype: str
        """
        try:
            return Codec._wrapped_decode(literal)
        except Exception:
            log.warning("Failed decoding literal. Forcing UTF-8 decoding")
            try:
                return Codec._wrapped_decode(literal, 'utf_8')
            except Exception:
                raise KiwiDecodingError(
                    'Locale setup is not utf-8 compatible'
                )

    @classmethod
    def _wrapped_decode(self, literal, charset=None):
        # This decode wrapper is only implemented to facilitate unit testing
        if charset:
            return literal.decode(charset)
        else:
            return literal.decode()
