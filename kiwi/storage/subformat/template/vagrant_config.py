# Copyright (c) 2019 SUSE Linux GmbH.  All rights reserved.
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
import os

from textwrap import dedent
from string import Template


class VagrantConfigTemplate(object):
    """
    **Generate a Vagrantfile configuration template**

    This class creates a simple template for the Vagrantfile that is included
    inside a vagrant box.

    The included Vagrantfile carries additional information for vagrant: by
    default that is just the boxes' MAC address, but depending on the provider
    additional information need to be present. These can be passed via the
    parameter ``custom_settings`` to the method :meth:`get_template`.

    Example usage:

    The default without any additional settings will result in this
    Vagrantfile:

    .. code:: python

        >>> vagrant_config = VagrantConfigTemplate()
        >>> print(
        ...     vagrant_config.get_template()
        ...     .substitute({'mac_address': 'deadbeef'})
        ... )
        Vagrant.configure("2") do |config|
          config.vm.base_mac = "deadbeef"
        end

    If your provider/box requires additional settings, provide them as follows:

    .. code:: python

        >>> extra_settings = dedent('''
        ... config.vm.hostname = "no-dead-beef"
        ... config.vm.provider :special do |special|
        ...   special.secret_settings = "please_work"
        ... end
        ... ''').strip()
        >>> print(
        ...     vagrant_config.get_template(extra_settings)
        ...     .substitute({'mac_address': 'DEADBEEF'})
        ... )
        Vagrant.configure("2") do |config|
          config.vm.base_mac = "DEADBEEF"
          config.vm.hostname = "no-dead-beef"
          config.vm.provider :special do |special|
            special.secret_settings = "please_work"
          end
        end
    """

    def __init__(self):
        self.indent = '  '

        self.header = dedent('''
            Vagrant.configure("2") do |config|
        ''').strip() + os.linesep

        self.mac = self.indent + dedent('''
            config.vm.base_mac = "${mac_address}"
        ''').strip() + os.linesep

        self.end = dedent('''
            end
        ''').strip()

    def get_template(self, custom_settings=None):
        """
        Return a new template with ``custom_settings`` included and
        indented appropriately.

        :param str custom_settings: String of additional settings that get
            pasted into the Vagrantfile template. The string is put at the
            correct indentation level for you, but the internal indentation has
            to be provided by the caller.
        :return: A template with ``custom_settings`` inserted at the
            appropriate position. The template has one the variable
            ``mac_address`` that must be substituted.
        :rtype: string.Template
        """
        template_data = self.header
        template_data += self.mac
        if custom_settings:
            template_data += self.indent
            template_data += self.indent.join(
                custom_settings.splitlines(True)
            )
            template_data += os.linesep
        template_data += self.end
        return Template(template_data)
