from unittest.mock import (
    patch, call, Mock
)
from collections import namedtuple

from kiwi.defaults import Defaults
from kiwi.boot.image.dracut import BootImageDracut
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.boot.image.base import boot_names_type


class TestBootImageKiwi:
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.dracut.Kernel')
    @patch('kiwi.boot.image.base.os.path.exists')
    def setup(self, mock_exists, mock_kernel_class, mock_cmd):
        Defaults.set_platform_name('x86_64')
        mock_exists.return_value = True
        kernel_type = namedtuple('kernel_type', ['version'])
        mock_kernel_instance = mock_kernel_class.return_value
        mock_kernel_instance.get_kernel.return_value = kernel_type(version='1.0.0-kernel')
        command_type = namedtuple('command', ['output'])
        mock_cmd.side_effect = [
            command_type(output='foo\nfoobar\nmodule'),  # for dracut --list-modules
            command_type(output='''
            kernel/drivers/net/ethernet/intel/driver2/driver2.ko: kernel/drivers/net/driver1.ko
            kernel/drivers/gpu/drm/i915/driver3.ko: kernel/drivers/video/other_driver/core/other_driver.ko
            kernel/drivers/usb/host/driver1.ko:
            ''')                                         # for cat modules.dep
        ]
        description = XMLDescription('../data/example_config.xml')
        self.xml_state = XMLState(
            description.load()
        )
        self.boot_image = BootImageDracut(
            self.xml_state, 'some-target-dir', 'system-directory'
        )
        assert mock_cmd.call_args_list == [
            call(['chroot', 'system-directory', 'dracut', '--list-modules', '--no-kernel']),
            call(['chroot', 'system-directory', 'cat', '/lib/modules/1.0.0-kernel/modules.dep'])
        ]

    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.base.os.path.exists')
    def setup_method(self, cls, mock_exists, mock_cmd):
        self.setup()

    @patch('kiwi.boot.image.dracut.SystemSetup')
    def test_prepare(self, mock_setup):
        setup = Mock()
        mock_setup.return_value = setup
        self.boot_image.prepare()
        setup.setup_machine_id.assert_called_once_with()
        assert self.boot_image.dracut_options == [
            '--install', '/.profile'
        ]

    def test_include_file(self):
        self.boot_image.include_file(filename='foo', delete_after_include=True)
        assert self.boot_image.included_files == [
            '--install', 'foo'
        ]
        assert self.boot_image.delete_after_include_files == [
            'foo'
        ]

    def test_include_module(self):
        self.boot_image.include_module('foobar')
        assert self.boot_image.add_modules == ['foobar']

        self.boot_image.include_module('foobar')
        self.boot_image.include_module('not_available')
        assert self.boot_image.add_modules == ['foobar']

    def test_omit_module(self):
        self.boot_image.omit_module('foobar')
        assert self.boot_image.omit_modules == ['foobar']

        self.boot_image.omit_module('foobar')
        assert self.boot_image.omit_modules == ['foobar']

    def test_set_static_modules(self):
        modules = ['foobar', 'module']
        self.boot_image.set_static_modules(modules)
        assert self.boot_image.modules == modules

    def test_include_driver(self):
        self.boot_image.include_driver('driver2')
        assert self.boot_image.add_drivers == ['driver2']

        self.boot_image.include_driver('driver2')
        self.boot_image.include_driver('not_available')
        assert self.boot_image.add_drivers == ['driver2']

    def test_omit_driver(self):
        self.boot_image.omit_driver('driver2')
        assert self.boot_image.omit_drivers == ['driver2']

        self.boot_image.omit_driver('driver2')
        assert self.boot_image.omit_drivers == ['driver2']

    def test_write_system_config_file(self):
        with patch('builtins.open', create=True) as mock_write:
            self.boot_image.write_system_config_file(
                config={
                    'modules': ['module'],
                    'omit_modules': ['foobar'],
                    'install_items': ['foo', 'bar'],
                    'drivers': ['driver3', 'driver2'],
                    'omit_drivers': ['driver1']
                },
                config_file='/root/dir/my_dracut_conf.conf'
            )
            assert call().__enter__().writelines(
                [
                    'add_dracutmodules+=" module "\n',
                    'omit_dracutmodules+=" foobar "\n',
                    'install_items+=" foo bar "\n',
                    'add_drivers+=" driver3 driver2 "\n',
                    'omit_drivers+=" driver1 "\n'
                ]
            ) in mock_write.mock_calls
            assert call(
                '/root/dir/my_dracut_conf.conf', 'w'
            ) in mock_write.mock_calls

        with patch('builtins.open', create=True) as mock_write:
            self.boot_image.write_system_config_file(
                config={
                    'modules': ['module'],
                    'omit_modules': ['foobar'],
                    'drivers': ['driver1', 'driver2'],
                    'omit_drivers': ['driver3']},
            )
            assert call().__enter__().writelines(
                [
                    'add_dracutmodules+=" module "\n',
                    'omit_dracutmodules+=" foobar "\n',
                    'add_drivers+=" driver1 driver2 "\n',
                    'omit_drivers+=" driver3 "\n'
                ]
            ) in mock_write.mock_calls
            assert call(
                'system-directory/etc/dracut.conf.d/02-kiwi.conf', 'w'
            ) in mock_write.mock_calls

    def test_include_file_install(self):
        self.boot_image.include_file('foo')
        assert self.boot_image.included_files == [
            '--install', 'foo'
        ]

    @patch('kiwi.boot.image.dracut.Kernel')
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.base.BootImageBase.is_prepared')
    @patch('kiwi.boot.image.dracut.Profile')
    @patch('kiwi.boot.image.dracut.MountManager')
    @patch('os.unlink')
    def test_create_uki(
        self, mock_os_unlink, mock_MountManager, mock_Profile,
        mock_prepared, mock_command, mock_kernel
    ):
        profile = Mock()
        profile.dot_profile = dict()
        mock_Profile.return_value = profile
        kernel = Mock()
        kernel_details = Mock()
        kernel_details.version = '1.2.3'
        kernel.get_kernel = Mock(return_value=kernel_details)
        mock_kernel.return_value = kernel
        self.boot_image.include_file(
            filename='system-directory/etc/foo', delete_after_include=True
        )
        self.boot_image.include_module('foo')
        self.boot_image.omit_module('bar')
        self.boot_image.include_driver('driver1')
        self.boot_image.include_driver('driver2')
        self.boot_image.omit_driver('driver3')
        self.boot_image.get_boot_names = Mock(
            return_value=boot_names_type(
                kernel_name='kernel_name',
                initrd_name='initrd-kernel_version',
                kernel_version='kernel_version',
                kernel_filename='kernel_filename'
            )
        )
        mock_prepared.return_value = False
        assert self.boot_image.create_uki('some_cmdline') == ''
        mock_prepared.return_value = True
        assert self.boot_image.create_uki('some_cmdline') == \
            'some-target-dir/kiwi.efi'
        profile.create.assert_called_once_with(
            'system-directory/.profile'
        )
        assert mock_MountManager.call_args_list == [
            call(device='/dev', mountpoint='system-directory/dev'),
            call(device='/proc', mountpoint='system-directory/proc')
        ]
        assert mock_command.call_args_list == [
            call(
                [
                    'chroot', 'system-directory',
                    'dracut',
                    '--no-hostonly',
                    '--no-hostonly-cmdline',
                    '--force',
                    '--verbose',
                    '--kver', '1.2.3',
                    '--uefi',
                    '--kernel-cmdline', 'some_cmdline',
                    '--add', ' foo ',
                    '--omit', ' bar ',
                    '--drivers', ' driver1 driver2 ',
                    '--omit-drivers', ' driver3 ',
                    '--install', 'system-directory/etc/foo',
                    'vmlinuz-kernel_version.efi'
                ], stderr_to_stdout=True),
            call(
                [
                    'mv', 'system-directory/vmlinuz-kernel_version.efi',
                    'some-target-dir/kiwi.efi'
                ]
            )
        ]
        mock_os_unlink.assert_called_once_with(
            'system-directory/system-directory/etc/foo'
        )

    @patch('kiwi.boot.image.dracut.Kernel')
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.base.BootImageBase.is_prepared')
    @patch('kiwi.boot.image.dracut.Profile')
    @patch('kiwi.boot.image.dracut.MountManager')
    @patch('os.unlink')
    def test_create_initrd(
        self, mock_os_unlink, mock_MountManager, mock_Profile,
        mock_prepared, mock_command, mock_kernel
    ):
        profile = Mock()
        profile.dot_profile = dict()
        mock_Profile.return_value = profile
        kernel = Mock()
        kernel_details = Mock()
        kernel_details.version = '1.2.3'
        kernel.get_kernel = Mock(return_value=kernel_details)
        mock_kernel.return_value = kernel
        self.boot_image.include_file(
            filename='system-directory/etc/foo', delete_after_include=True
        )
        self.boot_image.include_module('foo')
        self.boot_image.omit_module('bar')
        self.boot_image.include_driver('driver1')
        self.boot_image.omit_driver('driver2')
        self.boot_image.omit_driver('driver3')
        self.boot_image.create_initrd()
        profile.create.assert_called_once_with(
            'system-directory/.profile'
        )
        assert mock_MountManager.call_args_list == [
            call(device='/dev', mountpoint='system-directory/dev'),
            call(device='/proc', mountpoint='system-directory/proc')
        ]
        assert mock_command.call_args_list == [
            call(
                [
                    'chroot', 'system-directory',
                    'dracut', '--verbose', '--no-hostonly',
                    '--no-hostonly-cmdline',
                    '--add', ' foo ', '--omit', ' bar ',
                    '--drivers', ' driver1 ',
                    '--omit-drivers', ' driver2 driver3 ',
                    '--install', 'system-directory/etc/foo',
                    'LimeJeOS.x86_64-1.13.2.initrd', '1.2.3'
                ], stderr_to_stdout=True),
            call(
                [
                    'mv',
                    'system-directory/'
                    'LimeJeOS.x86_64-1.13.2.initrd',
                    'some-target-dir'
                ]
            ),
            call(
                ['chmod', '644', 'some-target-dir/LimeJeOS.x86_64-1.13.2.initrd']
            )
        ]
        mock_os_unlink.assert_called_once_with(
            'system-directory/system-directory/etc/foo'
        )
        mock_command.reset_mock()
        self.boot_image.create_initrd(basename='foo')
        assert mock_command.call_args_list == [
            call(
                [
                    'chroot', 'system-directory',
                    'dracut', '--verbose', '--no-hostonly',
                    '--no-hostonly-cmdline',
                    '--add', ' foo ', '--omit', ' bar ',
                    '--drivers', ' driver1 ',
                    '--omit-drivers', ' driver2 driver3 ',
                    '--install', 'system-directory/etc/foo',
                    'foo', '1.2.3'
                ], stderr_to_stdout=True),
            call(
                [
                    'mv',
                    'system-directory/foo',
                    'some-target-dir'
                ]
            ),
            call(
                ['chmod', '644', 'some-target-dir/foo']
            )
        ]

    def test_has_initrd_support(self):
        assert self.boot_image.has_initrd_support() is True

    def test_add_argument(self):
        self.boot_image.add_argument('option', 'value')
        assert self.boot_image.dracut_options == ['option', 'value']

    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.dracut.Kernel')
    def test_get_drivers(self, mock_kernel_class, mock_command):
        kernel_type = namedtuple('kernel_type', ['version'])
        mock_kernel_instance = mock_kernel_class.return_value
        mock_kernel_instance.get_kernel.return_value = kernel_type(version='1.0.0-kernel')

        mock_command.reset_mock()
        command_type = namedtuple('command', ['output'])
        mock_command.return_value = command_type(
            output='''
            kernel/drivers/net/ethernet/intel/driver2/driver2.ko: kernel/drivers/net/driver1.ko
            kernel/drivers/gpu/drm/i915/driver3.ko: kernel/drivers/video/fbdev/core/fb.ko
            kernel/drivers/usb/host/driver1.ko:
            kernel/drivers/vhost/driver_4.ko:
            '''
        )

        drivers = self.boot_image._get_drivers()

        mock_kernel_class.assert_called_once_with('system-directory')
        mock_kernel_instance.get_kernel.assert_called_once()
        mock_command.assert_called_once_with([
            'chroot', 'system-directory', 'cat',
            '/lib/modules/1.0.0-kernel/modules.dep'
        ])

        assert sorted(drivers) == sorted(['driver_4', 'driver3', 'driver2', 'driver1'])

    @patch('kiwi.boot.image.dracut.log.warning')
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.dracut.Kernel')
    @patch('kiwi.boot.image.base.os.path.exists')
    def test_get_drivers_no_kernel(self, mock_exists, mock_kernel_class, mock_command, mock_log_warning):
        mock_exists.return_value = True
        mock_kernel_instance = mock_kernel_class.return_value
        mock_kernel_instance.get_kernel.return_value = None

        drivers = self.boot_image._get_drivers()
        assert drivers == []  # Should return empty list when no kernel found

        mock_kernel_class.assert_called_once_with('system-directory')
        mock_kernel_instance.get_kernel.assert_called_once()
        mock_command.assert_not_called()
        mock_log_warning.assert_called_once_with("No kernel found in boot directory")

    @patch('kiwi.boot.image.dracut.log.warning')
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.dracut.Kernel')
    def test_get_drivers_with_exception(self, mock_kernel_class, mock_command, mock_log_warning):
        kernel_type = namedtuple('kernel_type', ['version'])
        mock_kernel_instance = mock_kernel_class.return_value
        mock_kernel_instance.get_kernel.return_value = kernel_type(version='1.0.0-kernel')
        mock_command.side_effect = Exception("Failed to read modules")

        drivers = self.boot_image._get_drivers()
        assert drivers == []  # Should return empty list on exception

        mock_kernel_class.assert_called_once_with('system-directory')
        mock_kernel_instance.get_kernel.assert_called_once()
        mock_command.assert_called_once_with([
            'chroot', 'system-directory', 'cat',
            '/lib/modules/1.0.0-kernel/modules.dep'
        ])
        mock_log_warning.assert_called_once_with("Error reading drivers: Failed to read modules")
