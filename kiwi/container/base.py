# Copyright (c) 2023 SUSE LLC
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
from abc import ABC, abstractmethod


class ContainerImageBase(ABC):
    @abstractmethod
    def create(
        self, filename: str, base_image: str,
        ensure_empty_tmpdirs: bool, compress_archive: bool = False
    ) -> str:
        pass  # pragma: no cover
