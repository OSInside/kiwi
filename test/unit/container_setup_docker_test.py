from nose.tools import *
from mock import patch
from mock import call
import mock

import kiwi

from . import nose_helper

from kiwi.exceptions import *
from kiwi.container.setup.docker import ContainerSetupDocker


class TestContainerSetupDocker(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.context_manager_mock = mock.MagicMock()
        self.file_mock = mock.MagicMock()
        self.enter_mock = mock.MagicMock()
        self.exit_mock = mock.MagicMock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        self.container = ContainerSetupDocker(
            'root_dir', {'container_name': 'system'}
        )

        self.container.create_fstab = mock.Mock()
        self.container.deactivate_bootloader_setup = mock.Mock()
        self.container.deactivate_root_filesystem_check = mock.Mock()
        self.container.setup_static_device_nodes = mock.Mock()
        self.container.setup_root_console = mock.Mock()
        self.container.deactivate_systemd_service = mock.Mock()

    @patch('builtins.open')
    @patch('kiwi.container.setup.docker.Path.create')
    @patch('kiwi.container.setup.docker.ContainerSetupDocker.create_lxc_fstab')
    @patch('kiwi.container.setup.docker.ContainerSetupDocker.create_lxc_config')
    def test_setup(self, mock_lxc_config, mock_lxc_fstab, mock_path, mock_open):
        self.container.setup()
        mock_path.assert_called_once_with('root_dir/etc/lxc')
        self.container.create_fstab.assert_called_once_with()
        self.container.deactivate_bootloader_setup.assert_called_once_with()
        self.container.deactivate_root_filesystem_check.assert_called_once_with()
        self.container.setup_static_device_nodes.assert_called_once_with()
        self.container.create_lxc_fstab.assert_called_once_with()
        self.container.create_lxc_config.assert_called_once_with()
        assert self.container.deactivate_systemd_service.call_args_list == [
            call('device-mapper.service'),
            call('kbd.service'),
            call('swap.service'),
            call('udev.service'),
            call('proc-sys-fs-binfmt_misc.automount')
        ]

    @patch('builtins.open')
    def test_create_lxc_fstab(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        self.container.create_lxc_fstab()
        mock_open.assert_called_once_with(
            'root_dir/etc/lxc/fstab', 'w'
        )
        assert self.file_mock.write.call_args_list == [
            call('proc /var/lib/lxc/system/rootfs/proc proc defaults 0 0\n'),
            call('sysfs /var/lib/lxc/system/rootfs/sys sysfs defaults 0 0\n')
        ]

    @patch('builtins.open')
    def test_create_lxc_config(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        self.container.create_lxc_config()
        mock_open.assert_called_once_with(
            'root_dir/etc/lxc/config', 'w'
        )
        assert self.file_mock.write.call_args_list == [
            call('lxc.mount.entry = /etc/resolv.conf /var/lib/lxc/system/rootfs/etc/resolv.conf none bind,ro 0 0\n'),
            call('lxc.network.type = veth\n'),
            call('lxc.network.flags = up\n'),
            call('lxc.network.link = br0\n'),
            call('lxc.network.name = eth0\n'),
            call('lxc.autodev = 1\n'),
            call('lxc.tty = 4\n'),
            call('lxc.kmsg = 0\n'),
            call('lxc.pts = 1024\n'),
            call('lxc.rootfs = /var/lib/lxc/system/rootfs\n'),
            call('lxc.mount = /etc/lxc/system/fstab\n'),
            call('lxc.cgroup.devices.deny = a\n'),
            call('lxc.cgroup.devices.allow = c 1:3 rwm\n'),
            call('lxc.cgroup.devices.allow = c 1:5 rwm\n'),
            call('lxc.cgroup.devices.allow = c 5:1 rwm\n'),
            call('lxc.cgroup.devices.allow = c 5:0 rwm\n'),
            call('lxc.cgroup.devices.allow = c 4:0 rwm\n'),
            call('lxc.cgroup.devices.allow = c 4:1 rwm\n'),
            call('lxc.cgroup.devices.allow = c 1:9 rwm\n'),
            call('lxc.cgroup.devices.allow = c 1:8 rwm\n'),
            call('lxc.cgroup.devices.allow = c 136:* rwm\n'),
            call('lxc.cgroup.devices.allow = c 5:2 rwm\n'),
            call('lxc.cgroup.devices.allow = c 254:0 rwm\n')
        ]

    def test_post_init(self):
        self.container.custom_args['container_name'] == 'system'
