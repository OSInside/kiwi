# Copyright (c) 2022 Marcus Schäfer.  All rights reserved.
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
import logging.handlers


class PlainTextSocketHandler(logging.handlers.SocketHandler):
    def makePickle(self, record):
        """
        Custom makePickle method which actually does not pickle
        the messages into the pickle binary format but just
        sends the log message as plain text. A simple server
        listening could then look like the following example

        .. code:: python

            sock_file = '/tmp/log_socket'
            buffer = 1024
            if os.path.exists(sock_file):
                os.unlink(sock_file)
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(sock_file)
            sock.listen(1)
            while True:
                connection, client_address = sock.accept()
                try:
                    while True:
                        data = connection.recv(buffer)
                        if not data:
                            break
                        print(data.decode())
                finally:
                    connection.close()
        """
        message = self.formatter.format(record)
        return message.encode()
