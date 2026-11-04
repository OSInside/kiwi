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
import requests

try:
    import progressbar2 as progressbar
except ImportError:
    import progressbar
import requests.packages.urllib3

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
            if content_length:
                widgets = [
                    'Loading: ',
                    progressbar.Percentage(),
                    ' ',
                    progressbar.Bar(marker='#', left='[', right=']'),
                    ' ',
                    progressbar.ETA(),
                    ' ',
                    progressbar.FileTransferSpeed(),
                ]
                maxval = int(content_length)
            else:
                # server did not send the size of the content
                widgets = ['Loading: ', progressbar.FileTransferSpeed()]
                maxval = progressbar.UnknownLength
            progress = progressbar.ProgressBar(
                maxval=maxval, widgets=widgets
            ).start()
            processed = 0
            with open(filename, 'wb') as data:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        data.write(chunk)
                        data.flush()
                        processed += len(chunk)
                        progress.update(processed)
            progress.finish()
        except requests.exceptions.RequestException as issue:
            raise KiwiUriOpenError(
                f'Download of {url} failed: {type(issue).__name__}: {issue}'
            )
