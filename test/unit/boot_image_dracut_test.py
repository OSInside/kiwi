import mock

from mock import patch
from mock import call
from collections import namedtuple

from .test_helper import patch_open, raises

from kiwi.boot.image.dracut import BootImageDracut
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState

from kiwi.exceptions import KiwiDiskBootImageError


class TestBootImageKiwi(object):
    @patch('kiwi.boot.image.base.os.path.exists')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_exists):
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        mock_machine.return_value = 'x86_64'
        mock_exists.return_value = True
        description = XMLDescription('../data/example_config.xml')
        self.xml_state = XMLState(
            description.load()
        )
        self.boot_image = BootImageDracut(
            self.xml_state, 'some-target-dir', 'system-directory'
        )

    @patch('kiwi.boot.image.dracut.SystemSetup')
    @patch('kiwi.boot.image.dracut.Profile')
    def test_prepare(self, mock_profile, mock_setup):
        setup = mock.Mock()
        profile = mock.Mock()
        profile.dot_profile = dict()
        mock_profile.return_value = profile
        mock_setup.return_value = setup
        self.boot_image.prepare()
        setup.import_shell_environment.assert_called_once_with(profile)
        setup.setup_machine_id.assert_called_once_with()
        assert self.boot_image.dracut_options == [
            '--install', '/.profile'
        ]

    def test_include_file(self):
        self.boot_image.include_file('foo')
        assert self.boot_image.dracut_options == [
            '--install', 'foo'
        ]

    @patch('kiwi.boot.image.dracut.Kernel')
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.base.BootImageBase.is_prepared')
    def test_create_initrd(
        self, mock_prepared, mock_command, mock_kernel
    ):
        kernel = mock.Mock()
        kernel_details = mock.Mock()
        kernel_details.version = '1.2.3'
        kernel.get_kernel = mock.Mock(return_value=kernel_details)
        mock_kernel.return_value = kernel
        self.boot_image.include_file('system-directory/etc/foo')
        self.boot_image.include_file('/system-directory/var/lib/bar')
        self.boot_image.create_initrd()
        assert mock_command.call_args_list == [
            call([
                'chroot', 'system-directory',
                'dracut', '--force', '--no-hostonly',
                '--no-hostonly-cmdline', '--xz',
                '--install', 'system-directory/etc/foo',
                '--install', '/system-directory/var/lib/bar',
                'LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd.xz', '1.2.3'
            ]),
            call([
                'mv',
                'system-directory/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd.xz',
                'some-target-dir'
            ])
        ]
        mock_command.reset_mock()
        self.boot_image.create_initrd(basename='foo')
        assert mock_command.call_args_list == [
            call([
                'chroot', 'system-directory',
                'dracut', '--force', '--no-hostonly',
                '--no-hostonly-cmdline', '--xz',
                '--install', 'system-directory/etc/foo',
                '--install', '/system-directory/var/lib/bar',
                'foo.xz', '1.2.3'
            ]),
            call([
                'mv',
                'system-directory/foo.xz',
                'some-target-dir'
            ])
        ]

    @raises(KiwiDiskBootImageError)
    @patch('kiwi.boot.image.dracut.Kernel')
    def test_get_boot_names_raises(self, mock_Kernel):
        kernel = mock.Mock()
        mock_Kernel.return_value = kernel
        kernel.get_kernel.return_value = None
        self.boot_image.get_boot_names()

    @patch_open
    @patch('kiwi.boot.image.dracut.Kernel')
    @patch('kiwi.boot.image.dracut.Path.which')
    @patch('kiwi.boot.image.dracut.log.warning')
    def test_get_boot_names(
        self, mock_warning, mock_Path_which, mock_Kernel, mock_open
    ):
        boot_names_type = namedtuple(
            'boot_names_type', ['kernel_name', 'initrd_name']
        )
        mock_Path_which.return_value = 'dracut'
        kernel = mock.Mock()
        kernel_info = mock.Mock()
        kernel_info.name = 'kernel_name'
        kernel_info.version = 'kernel_version'
        kernel.get_kernel.return_value = kernel_info
        mock_Kernel.return_value = kernel

        self.file_mock.read.return_value = 'outfile="/boot/initrd-$kernel"'

        mock_open.return_value = self.context_manager_mock

        assert self.boot_image.get_boot_names() == boot_names_type(
            kernel_name='kernel_name',
            initrd_name='initrd-kernel_version'
        )

        self.file_mock.read.return_value = 'outfile="foo"'

        assert self.boot_image.get_boot_names() == boot_names_type(
            kernel_name='kernel_name',
            initrd_name='initramfs-kernel_version.img'
        )
