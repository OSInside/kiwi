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
from typing import List, Optional

import requests
import requests.packages.urllib3
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    ProgressColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from kiwi.exceptions import KiwiUriOpenError


class FetchFiles:
    """
    **Fetch File Manager**

    Fetches file(s) from a given URL to the local system
    """

    def __init__(self) -> None:
        requests.packages.urllib3.disable_warnings()

    def wget(self, url: str, filename: str, chunk_size: int = 4096) -> None:
        """
        Download content of given url to filename

        :param str url: URI
        :param str filename: local file path name

        :raises KiwiUriOpenError: if the download fails
        """
        try:
            response = requests.request(
                'GET', url, stream=True, data=None, headers=None
            )
            response.raise_for_status()
            content_length = response.headers.get('Content-Length')
            total: Optional[int]
            columns: List[ProgressColumn]
            if content_length:
                total = int(content_length)
                columns = [
                    TextColumn('Loading:'),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                    TransferSpeedColumn(),
                ]
            else:
                # server did not send the size of the content
                total = None
                columns = [
                    TextColumn('Loading:'),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                ]
            with Progress(*columns) as progress:
                task = progress.add_task('Loading', total=total)
                with open(filename, 'wb') as data:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            data.write(chunk)
                            data.flush()
                            progress.update(task, advance=len(chunk))
        except requests.exceptions.RequestException as issue:
            raise KiwiUriOpenError(
                f'Download of {url} failed: {type(issue).__name__}: {issue}'
            )
