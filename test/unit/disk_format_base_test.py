from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.disk_format_base import DiskFormatBase


class TestDiskFormatBase(object):
    def setup(self):
        xml_data = mock.Mock()
        xml_data.get_name = mock.Mock(
            return_value='some-disk-image'
        )
        self.xml_state = mock.Mock()
        self.xml_state.xml_data = xml_data
        self.disk_format = DiskFormatBase(
            self.xml_state, 'source_dir', 'target_dir'
        )

    @raises(NotImplementedError)
    def test_create_image_format(self):
        self.disk_format.create_image_format()

    @raises(KiwiFormatSetupError)
    def test_get_target_name_for_format_invalid_format(self):
        self.disk_format.get_target_name_for_format('foo')

    def test_post_init(self):
        self.disk_format.post_init({'option': 'unhandled'})
        assert self.disk_format.custom_args == {}

    def test_get_target_name_for_format(self):
        assert self.disk_format.get_target_name_for_format('vhd') == \
            'target_dir/some-disk-image.vhd'
