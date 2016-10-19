import sys
import mock
from mock import call

import kiwi

from .test_helper import raises, patch

from kiwi.exceptions import KiwiImageResizeError, KiwiConfigFileNotFound

from kiwi.tasks.image_resize import ImageResizeTask


class TestImageResizeTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], '--type', 'vmx', 'image', 'resize',
            '--target-dir', 'target_dir', '--size', '20g',
            '--root', '../data/root-dir'
        ]
        kiwi.tasks.image_resize.Help = mock.Mock(
            return_value=mock.Mock()
        )

        self.image_format = mock.Mock()
        self.image_format.has_raw_disk = mock.Mock()
        self.image_format.diskname = 'some-disk.raw'
        kiwi.tasks.image_resize.DiskFormat = mock.Mock(
            return_value=self.image_format
        )

        self.task = ImageResizeTask()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['resize'] = False
        self.task.command_args['--target-dir'] = 'target_dir'
        self.task.command_args['--size'] = '42g'
        self.task.command_args['--root'] = '../data/root-dir'

    @raises(KiwiConfigFileNotFound)
    def test_process_no_root_directory_specified(self):
        self.task.command_args['--root'] = None
        self.task.process()

    @raises(KiwiImageResizeError)
    def test_process_no_raw_disk_found(self):
        self._init_command_args()
        self.image_format.has_raw_disk.return_value = False
        self.task.command_args['resize'] = True
        self.task.process()

    @raises(KiwiImageResizeError)
    def test_process_unsupported_size_format(self):
        self._init_command_args()
        self.task.command_args['--size'] = '20x'
        self.image_format.has_raw_disk.return_value = True
        self.task.command_args['resize'] = True
        self.task.process()

    def test_process_image_resize_gb(self):
        self._init_command_args()
        self.task.command_args['resize'] = True
        self.image_format.resize_raw_disk.return_value = True
        self.task.process()
        self.image_format.resize_raw_disk.assert_called_once_with(
            42 * 1024 * 1024 * 1024
        )
        self.image_format.create_image_format.assert_called_once_with()

    def test_process_image_resize_mb(self):
        self._init_command_args()
        self.task.command_args['resize'] = True
        self.task.command_args['--size'] = '42m'
        self.image_format.resize_raw_disk.return_value = True
        self.task.process()
        self.image_format.resize_raw_disk.assert_called_once_with(
            42 * 1024 * 1024
        )
        self.image_format.create_image_format.assert_called_once_with()

    def test_process_image_resize_bytes(self):
        self._init_command_args()
        self.task.command_args['resize'] = True
        self.task.command_args['--size'] = '42'
        self.image_format.resize_raw_disk.return_value = True
        self.task.process()
        self.image_format.resize_raw_disk.assert_called_once_with(
            42
        )
        self.image_format.create_image_format.assert_called_once_with()

    @patch('kiwi.logger.log.info')
    def test_process_image_resize_not_needed(self, mock_log_info):
        self._init_command_args()
        self.task.command_args['resize'] = True
        self.task.command_args['--size'] = '42'
        self.image_format.resize_raw_disk.return_value = False
        self.task.process()
        self.image_format.resize_raw_disk.assert_called_once_with(
            42
        )
        assert mock_log_info.call_args_list == [
            call('Loading XML description'),
            call('--> loaded %s', '../data/root-dir/image/config.xml'),
            call('--> Selected build type: %s', 'vmx'),
            call('--> Selected profiles: %s', 'vmxFlavour'),
            call('Resizing raw disk to 42 bytes'),
            call('Raw disk is already at 42 bytes')
        ]

    def test_process_image_resize_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['resize'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::image::resize'
        )
