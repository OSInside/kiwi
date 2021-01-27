# Copyright (c) 2021 SUSE Software Solutions Germany GmbH. All rights reserved.
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
import warnings
from functools import wraps
from typing import Callable


def obsolete(decommission_at: str, version: str) -> Callable:
    """
    Decorator method to mark an API method as obsolete

    Methods marked with this decorator are still called.
    If the provided decommission date is reached it is
    allowed to decorate the obsoleted method as
    decommissioned.

    Example:

        .. code:: python

            @obsolete(decommission_at='2025-01-28', version='1.2.3')
            def method():
                print('Method implementation...')

    :param str decommission_at: decommision date string.
    :param str version: the first version when this function was deprecated.

    :return: decorated function which is marked as deprecated
    """
    def decorate_obsolete(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f'Function {func.__name__!r} is marked obsolete '
                f'since version {version!r} '
                f'and will be decommissioned at: {decommission_at}'
            )
            return func(*args, **kwargs)
        return wrapper
    return decorate_obsolete


def decommissioned(func: Callable) -> Callable:
    """
    Decorator method to mark an API method as decommissioned

    Methods marked with this decorator are no longer called
    and raises DeprecationWarning when used.
    The method implementation is allowed to be replaced by
    a simple pass statement to get rid of old code

    Example:

        .. code:: python

            @decommissioned
            def method():
                pass

    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        raise DeprecationWarning(
            f'Function {func.__name__!r} has been decommissioned'
        )
    return wrapper
