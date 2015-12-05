from nose.tools import *
from mock import patch
from mock import call
import mock
import kiwi

import nose_helper

from kiwi.exceptions import *
from kiwi.install_image_builder import InstallImageBuilder


class TestInstallImageBuilder(object):
    def setup(self):
        self.bootloader = mock.Mock()
        kiwi.install_image_builder.BootLoaderConfig.new = mock.Mock(
            return_value=self.bootloader
        )
        self.squashed_image = mock.Mock()
        kiwi.install_image_builder.FileSystemSquashFs = mock.Mock(
            return_value=self.squashed_image
        )
        self.mbrid = mock.Mock()
        self.mbrid.get_id = mock.Mock(
            return_value='0xffffffff'
        )
        kiwi.install_image_builder.ImageIdentifier = mock.Mock(
            return_value=self.mbrid
        )
        kiwi.install_image_builder.Path = mock.Mock()
        self.checksum = mock.Mock()
        kiwi.install_image_builder.Checksum = mock.Mock(
            return_value=self.checksum
        )
        self.xml_state = mock.Mock()
        self.boot_image_task = mock.Mock()
        self.boot_image_task.boot_root_directory = 'initrd_dir'
        self.boot_image_task.initrd_filename = 'initrd'
        self.install_image = InstallImageBuilder(
            self.xml_state, 'target_dir', 'some-kernel',
            'some-diskimage', self.boot_image_task
        )

    @patch('kiwi.install_image_builder.mkdtemp')
    @patch('__builtin__.open')
    @patch('kiwi.install_image_builder.Command.run')
    def test_create_install_iso(self, mock_command, mock_open, mock_dtemp):
        mock_dtemp.return_value = 'tmpdir'
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.install_image.create_install_iso()

        self.checksum.md5.assert_called_once_with(
            'initrd_dir/etc/image.md5'
        )
        assert mock_open.call_args_list == [
            call('initrd_dir/config.vmxsystem', 'w'),
            call('tmpdir/config.isoclient', 'w')
        ]
        assert file_mock.write.call_args_list == [
            call('IMAGE="some-diskimage"\n'),
            call('IMAGE="some-diskimage"\n')
        ]
        self.squashed_image.create_on_file.assert_called_once_with(
            'some-diskimage.squashfs'
        )
        self.bootloader.setup_install_boot_images.assert_called_once_with(
            lookup_path='initrd_dir', mbrid=self.mbrid
        )
        self.bootloader.setup_install_image_config.assert_called_once_with(
            self.mbrid
        )
        self.bootloader.write.assert_called_once_with()
        self.boot_image_task.create_initrd.assert_called_once_with(
            self.mbrid
        )
        assert mock_command.call_args_list == [
            call(['mv', 'some-diskimage.squashfs', 'tmpdir']),
            call(['cp', 'some-kernel', 'tmpdir/boot/x86_64/loader/linux']),
            call(['mv', 'initrd', 'tmpdir/boot/x86_64/loader/initrd'])
        ]

    def test_create_install_pxe_archive(self):
        # TODO
        self.install_image.create_install_pxe_archive()

    def test_destructor(self):
        # TODO
        self.install_image.__del__()
