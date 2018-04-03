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
import os
from string import Template
from textwrap import dedent


class PackageManagerTemplateAptGet(object):
    """
    apt-get configuration file template
    """
    def __init__(self):
        self.host_header = dedent('''
            # kiwi generated apt-get config file
            Dir "/";
            Dir::State "${apt_shared_base}/";
            Dir::Cache "${apt_shared_base}/";
            Dir::Etc   "${apt_shared_base}/";
        ''').strip() + os.linesep

        self.image_header = dedent('''
            # kiwi generated apt-get config file
            Dir "/";
        ''').strip() + os.linesep

        self.apt = dedent('''
            APT
            {
                Get
                {
                    AllowDowngrades "true";
                    AllowRemoveEssential "true";
                    AllowChangeHeldPackages "true";
                    AllowUnauthenticated "${unauthenticated}";
                }
            };
        ''').strip() + os.linesep

        self.dpkg_exclude_docs = dedent('''
            DPkg::Options {
                "--path-exclude=/usr/share/man/*";
                "--path-exclude=/usr/share/doc/*";
                "--path-include=/usr/share/doc/*/copyright";
            };
        ''').strip() + os.linesep

    def get_host_template(self, exclude_docs=False):
        """
        apt-get package manager template for apt-get called
        outside of the image, not chrooted

        :rtype: Template
        """
        template_data = self.host_header + self.apt
        if exclude_docs:
            template_data += self.dpkg_exclude_docs

        return Template(template_data)

    def get_image_template(self, exclude_docs=False):
        """
        apt-get package manager template for apt-get called
        inside of the image, chrooted

        :rtype: Template
        """
        template_data = self.image_header + self.apt
        if exclude_docs:
            template_data += self.dpkg_exclude_docs

        return Template(template_data)
