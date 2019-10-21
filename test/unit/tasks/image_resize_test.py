import logging
import os
import sys
from mock import Mock
from pytest import (
    raises, fixture
)

from ..test_helper import argv_kiwi_tests

import kiwi
from kiwi.tasks.image_resize import ImageResizeTask

from kiwi.exceptions import (
    KiwiImageResizeError,
    KiwiSizeError,
    KiwiConfigFileNotFound
)


class TestImageResizeTask:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        sys.argv = [
            sys.argv[0], '--type', 'vmx', 'image', 'resize',
            '--target-dir', 'target_dir', '--size', '20g',
            '--root', '../data/root-dir'
        ]
        self.abs_root_dir = os.path.abspath('../data/root-dir')

        kiwi.tasks.image_resize.Help = Mock(
            return_value=Mock()
        )

        self.firmware = Mock()
        self.firmware.get_partition_table_type = Mock(
            return_value='gpt'
        )
        self.partitioner = Mock()
        self.loop_provider = Mock()
        self.image_format = Mock()
        self.image_format.has_raw_disk = Mock()
        self.image_format.diskname = 'some-disk.raw'
        kiwi.tasks.image_resize.DiskFormat = Mock(
            return_value=self.image_format
        )
        kiwi.tasks.image_resize.FirmWare = Mock(
            return_value=self.firmware
        )
        kiwi.tasks.image_resize.LoopDevice = Mock(
            return_value=self.loop_provider
        )
        kiwi.tasks.image_resize.Partitioner = Mock(
            return_value=self.partitioner
        )

        self.task = ImageResizeTask()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['resize'] = False
        self.task.command_args['--target-dir'] = 'target_dir'
        self.task.command_args['--size'] = '42g'
        self.task.command_args['--root'] = '../data/root-dir'

    def test_process_no_root_directory_specified(self):
        self.task.command_args['--root'] = None
        with raises(KiwiConfigFileNotFound):
            self.task.process()

    def test_process_no_raw_disk_found(self):
        self._init_command_args()
        self.image_format.has_raw_disk.return_value = False
        self.task.command_args['resize'] = True
        with raises(KiwiImageResizeError):
            self.task.process()

    def test_process_unsupported_size_format(self):
        self._init_command_args()
        self.task.command_args['--size'] = '20x'
        self.image_format.has_raw_disk.return_value = True
        self.task.command_args['resize'] = True
        with raises(KiwiSizeError):
            self.task.process()

    def test_process_image_resize_gb(self):
        self._init_command_args()
        self.task.command_args['resize'] = True
        self.image_format.resize_raw_disk.return_value = True
        self.task.process()
        self.loop_provider.create.assert_called_once_with(overwrite=False)
        self.partitioner.resize_table.assert_called_once_with()
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
        self.loop_provider.create.assert_called_once_with(overwrite=False)
        self.partitioner.resize_table.assert_called_once_with()
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
        self.loop_provider.create.assert_called_once_with(overwrite=False)
        self.partitioner.resize_table.assert_called_once_with()
        self.image_format.resize_raw_disk.assert_called_once_with(
            42
        )
        self.image_format.create_image_format.assert_called_once_with()

    def test_process_image_resize_not_needed(self):
        self._init_command_args()
        self.task.command_args['resize'] = True
        self.task.command_args['--size'] = '42'
        self.image_format.resize_raw_disk.return_value = False
        with self._caplog.at_level(logging.INFO):
            self.task.process()
            self.loop_provider.create.assert_called_once_with(overwrite=False)
            self.partitioner.resize_table.assert_called_once_with()
            self.image_format.resize_raw_disk.assert_called_once_with(
                42
            )
            assert 'Loading XML description' in self._caplog.text
            assert '--> loaded {0}'.format(
                os.sep.join([self.abs_root_dir, 'image', 'config.xml'])
            ) in self._caplog.text
            assert '--> Selected build type: vmx' in self._caplog.text
            assert '--> Selected profiles: vmxFlavour' in self._caplog.text
            assert 'Resizing raw disk to 42 bytes' in self._caplog.text
            assert 'Raw disk is already at 42 bytes' in self._caplog.text

    def test_process_image_resize_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['resize'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::image::resize'
        )
