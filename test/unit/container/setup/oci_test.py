from mock import patch
from mock import call
import mock

from kiwi.container.setup.oci import ContainerSetupOCI


class TestContainerSetupOCI:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True

        self.container = ContainerSetupOCI(
            'root_dir', {'container_name': 'system'}
        )

        self.container.deactivate_bootloader_setup = mock.Mock()
        self.container.deactivate_root_filesystem_check = mock.Mock()
        self.container.setup_static_device_nodes = mock.Mock()
        self.container.setup_root_console = mock.Mock()
        self.container.deactivate_systemd_service = mock.Mock()

    def test_setup(self):
        self.container.setup()
        self.container.deactivate_bootloader_setup.assert_called_once_with()
        self.container.deactivate_root_filesystem_check.assert_called_once_with()
        self.container.setup_static_device_nodes.assert_called_once_with()
        assert self.container.deactivate_systemd_service.call_args_list == [
            call('device-mapper.service'),
            call('kbd.service'),
            call('swap.service'),
            call('udev.service'),
            call('proc-sys-fs-binfmt_misc.automount')
        ]

    def test_post_init(self):
        self.container.custom_args['container_name'] == 'system'
