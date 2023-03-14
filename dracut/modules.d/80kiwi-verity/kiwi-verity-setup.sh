#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2023 Canonical Ltd
# Author: Isaac True <isaac.true@canonical.com>
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
# shellcheck disable=SC1091
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

if ! getarg "verityroot="; then
    return
fi

VERITY_ROOT=$(getarg "verityroot=")

if [ ! -e "${VERITY_ROOT}" ]; then
    # Source device does not exist (yet?)
    exit 1
fi

if [ -e "/dev/mapper/verityRoot" ]; then
    # Mapping already exists - we don't need to do it again
    exit 0
fi

ROOT_HASH=$(kiwi-parse-verity -p "${VERITY_ROOT}" -o root-hash)
ALGORITHM=$(kiwi-parse-verity -p "${VERITY_ROOT}" -o algorithm)
HASH_TYPE=$(kiwi-parse-verity -p "${VERITY_ROOT}" -o hash-type)
HASH_BLOCK_SIZE=$(kiwi-parse-verity -p "${VERITY_ROOT}" -o hash-blocksize)
DATA_BLOCK_SIZE=$(kiwi-parse-verity -p "${VERITY_ROOT}" -o data-blocksize)
SALT=$(kiwi-parse-verity -p "${VERITY_ROOT}" -o salt)
DATA_BLOCKS=$(kiwi-parse-verity -p "${VERITY_ROOT}" -o data-blocks)
HASH_START_BLOCK=$(kiwi-parse-verity -p "${VERITY_ROOT}" -o hash-start-block)
HASH_OFFSET=$(( "${HASH_START_BLOCK}" * "${HASH_BLOCK_SIZE}" ))

veritysetup open "${VERITY_ROOT}" verityRoot "${VERITY_ROOT}" "${ROOT_HASH}" \
    --no-superblock --hash "${ALGORITHM}" --format "${HASH_TYPE}" \
    --hash-block-size "${HASH_BLOCK_SIZE}" --data-block-size "${DATA_BLOCK_SIZE}" \
    --salt "${SALT}" --data-blocks "${DATA_BLOCKS}" --hash-offset "${HASH_OFFSET}"
