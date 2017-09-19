import mock

from mock import patch
from mock import call

from kiwi.boot.image.dracut import BootImageDracut
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState


class TestBootImageKiwi(object):
    @patch('kiwi.boot.image.base.os.path.exists')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_exists):
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
        mock_profile.return_value = profile
        mock_setup.return_value = setup
        self.boot_image.prepare()
        setup.import_shell_environment.assert_called_once_with(profile)
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
