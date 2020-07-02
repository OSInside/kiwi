# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
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
# project
from .tasks.base import CliTask


class App:
    """
    **Implements creation of task instances**

    Each task class implements a process method which is called
    when constructing an instance of App
    """
    def __init__(self):
        app = CliTask(should_perform_task_setup=False)
        action = app.cli.get_command()
        service = app.cli.get_servicename()
        task_class_name = service.title() + action.title() + 'Task'
        task_class = app.task.__dict__[task_class_name]
        task_class().process()
