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
from kiwi.defaults import Defaults


class IsoToolsBase(object):
    """
    Base Class for Parameter API for iso creation tools

    Attributes

    * :attr:`boot_path`
        architecture specific boot path on the ISO

    * :attr:`iso_parameters`
        list of ISO creation parameters

    * :attr:`iso_loaders`
        list of ISO loaders to embed
    """
    def __init__(self, source_dir):
        """
        Initialize setup data for later iso creation tool

        :param string source_dir: data source dir, usually root_dir
        """
        self.source_dir = source_dir

        self.boot_path = Defaults.get_iso_boot_path()
        self.iso_parameters = []
        self.iso_loaders = []

    def get_tool_name(self):
        """
        Return caller name for iso creation tool

        Implementation in specialized tool class

        :return: tool name
        """
        raise NotImplementedError

    def init_iso_creation_parameters(self, sortfile, custom_args=None):
        """
        Create a set of standard parameters for the main isolinux loader

        Implementation in specialized tool class

        :param string sortfile: unused
        :param list custom_args: unused
        """
        raise NotImplementedError

    def add_efi_loader_parameters(self):
        """
        Add ISO creation parameters to embed the EFI loader

        Implementation in specialized tool class
        """
        raise NotImplementedError

    def create_iso(self, filename, hidden_files=None):
        """
        Create iso file

        Implementation in specialized tool class

        :param string filename: unused
        """
        raise NotImplementedError

    def list_iso(self, isofile):
        """
        List contents of an ISO image

        :param string isofile: unused
        """
        raise NotImplementedError

    def has_iso_hybrid_capability(self):
        """
        Indicate if the iso tool has the capability to embed
        a partition table into the iso such that it can be
        used as both; an iso and a disk

        Implementation in specialized tool class
        """
        raise NotImplementedError
