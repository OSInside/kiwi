#!/bin/sh
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

if [ ! -e "/etc/veritytab" ];then
    return
fi

read -r name data_device hash_device root_hash options < /etc/veritytab

if [ "$(echo "${data_device}" | cut -f1 -d=)" = "UUID" ];then
    data_device=/dev/disk/by-uuid/$(echo "${data_device}" | cut -f2 -d=)
fi
if [ "$(echo "${hash_device}" | cut -f1 -d=)" = "UUID" ];then
    hash_device=/dev/disk/by-uuid/$(echo "${hash_device}" | cut -f2 -d=)
fi

veritysetup="veritysetup open "
veritysetup="${veritysetup} ${data_device} ${name} ${hash_device} ${root_hash}"

for option in $(echo "${options}" | tr , " ");do
    veritysetup="${veritysetup} --${option}"
done

eval "${veritysetup}"
