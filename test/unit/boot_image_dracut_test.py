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

    def test_prepare(self):
        # just pass, there is nothing we need to do for dracut here
        self.boot_image.prepare()

    @patch('kiwi.boot.image.dracut.Compress')
    @patch('kiwi.boot.image.dracut.Kernel')
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.base.BootImageBase.is_prepared')
    def test_create_initrd(
        self, mock_prepared, mock_command, mock_kernel, mock_compress
    ):
        kernel = mock.Mock()
        kernel_details = mock.Mock()
        kernel_details.version = '1.2.3'
        kernel.get_kernel = mock.Mock(return_value=kernel_details)
        mock_kernel.return_value = kernel
        compress = mock.Mock()
        mock_compress.return_value = compress
        self.boot_image.create_initrd()
        assert mock_command.call_args_list == [
            call([
                'chroot', 'system-directory',
                'dracut', '--force', '--no-hostonly',
                '--no-hostonly-cmdline', '--no-compress',
                'LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd', '1.2.3'
            ]),
            call([
                'mv',
                'system-directory/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd',
                'some-target-dir/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd'
            ])
        ]
        mock_compress.assert_called_once_with(
            self.boot_image.target_dir +
            '/LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd'
        )
        compress.xz.assert_called_once_with()
