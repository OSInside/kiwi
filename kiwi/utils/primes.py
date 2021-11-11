# Copyright (c) 2021 SUSE Linux GmbH.  All rights reserved.
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

import math

from typing import List, Iterator

# initial list of prime numbers which will be extended as much as required
# and reused in next calls

_primes: List[int] = [2, 3, 5, 7, 11, 13, 17]


def _update_primes(n: int) -> None:
    """
    Extend the list of prime numbers if required.
    """
    global _primes
    if n <= _primes[-1]:
        return
    _n = int(math.ceil(n**0.5))
    _update_primes(_n)

    start = _primes[-1] + 1
    for i in range(start, n + 1):
        if all(i % p for p in primes(_n)):
            _primes.append(i)


def primes(number: int) -> Iterator[int]:
    """
    Get prime numbers no greater than given number.

    :param int number: highest possible number to return.

    :rtype: int generator
    """
    global _primes
    _update_primes(number)
    for p in _primes:
        if p <= number:
            yield p
        else:
            break


def factors(number: int, max_factor: int = None) -> Iterator[int]:
    _max = int(math.ceil(number**0.5))
    _max = min(_max, max_factor or _max)
    _number = number
    for i in primes(_max):
        while _number % i == 0 and i <= _max:
            _number = _number // i
            _max = min(_max, int(math.ceil(_number**0.5)))
            yield i
    if _number != 1:
        if not max_factor or _number <= max_factor:
            yield _number
