from nose.tools import *
from mock import patch

import mock

from . import nose_helper

from kiwi.exceptions import *
from kiwi.internal_boot_image_task import BootImageTask


class TestInternalBootImageTask(object):
    @raises(KiwiBootImageSetupError)
    def test_boot_image_task_not_implemented(self):
        BootImageTask('foo', mock.Mock(), 'target_dir')

    @patch('kiwi.internal_boot_image_task.BootImageKiwi')
    def test_boot_image_task_kiwi(self, mock_kiwi):
        xml_state = mock.Mock()
        BootImageTask('kiwi', xml_state, 'target_dir')
        mock_kiwi.assert_called_once_with(
            xml_state, 'target_dir', None
        )
