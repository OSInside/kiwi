# Copyright (c) 2021 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from typing import Optional
from getpass import getpass


class Credentials:
    def __init__(self):
        self.obs_pass: Optional[str] = None

    def get_obs_credentials(self, user: str) -> str:
        if not self.obs_pass:
            self.obs_pass = getpass(f'Enter OBS password for {user}: ')
        return self.obs_pass
