#!/bin/bash
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
declare moddir=${moddir}

check() {
    require_binaries /usr/bin/kiwi-parse-verity || return 1
    require_binaries /usr/sbin/veritysetup || return 1
}

depends() {
    return 0
}

install() {
    inst_multiple /usr/bin/kiwi-parse-verity /usr/sbin/veritysetup
    inst_hook initqueue/settled 70 "$moddir/kiwi-verity-setup.sh"
}
