from unittest.mock import (
    patch, call, Mock
)
from collections import namedtuple

from kiwi.defaults import Defaults
from kiwi.boot.image.dracut import BootImageDracut
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState


class TestBootImageKiwi:
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.base.os.path.exists')
    def setup(self, mock_exists, mock_cmd):
        Defaults.set_platform_name('x86_64')
        mock_exists.return_value = True
        command_type = namedtuple('command', ['output'])
        mock_cmd.return_value = command_type(
            output='foo\nfoobar\nmodule'
        )
        description = XMLDescription('../data/example_config.xml')
        self.xml_state = XMLState(
            description.load()
        )
        self.boot_image = BootImageDracut(
            self.xml_state, 'some-target-dir', 'system-directory'
        )
        mock_cmd.assert_called_once_with([
            'chroot', 'system-directory', 'dracut',
            '--list-modules', '--no-kernel'
        ])

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
        self.boot_image.include_file('foo')
        assert self.boot_image.included_files == [
            '--install', 'foo'
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

    def test_write_system_config_file(self):
        with patch('builtins.open', create=True) as mock_write:
            self.boot_image.write_system_config_file(
                config={
                    'modules': ['module'],
                    'omit_modules': ['foobar'],
                    'install_items': ['foo', 'bar']
                },
                config_file='/root/dir/my_dracut_conf.conf'
            )
            assert call().__enter__().writelines(
                [
                    'add_dracutmodules+=" module "\n',
                    'omit_dracutmodules+=" foobar "\n',
                    'install_items+=" foo bar "\n',
                ]
            ) in mock_write.mock_calls
            assert call(
                '/root/dir/my_dracut_conf.conf', 'w'
            ) in mock_write.mock_calls

        with patch('builtins.open', create=True) as mock_write:
            self.boot_image.write_system_config_file(
                config={'modules': ['module'], 'omit_modules': ['foobar']},
            )
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
    def test_create_initrd(
        self, mock_MountManager, mock_Profile, mock_prepared,
        mock_command, mock_kernel
    ):
        profile = Mock()
        profile.dot_profile = dict()
        mock_Profile.return_value = profile
        kernel = Mock()
        kernel_details = Mock()
        kernel_details.version = '1.2.3'
        kernel.get_kernel = Mock(return_value=kernel_details)
        mock_kernel.return_value = kernel
        self.boot_image.include_file('system-directory/etc/foo')
        self.boot_image.include_module('foo')
        self.boot_image.omit_module('bar')
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
        mock_command.reset_mock()
        self.boot_image.create_initrd(basename='foo')
        assert mock_command.call_args_list == [
            call(
                [
                    'chroot', 'system-directory',
                    'dracut', '--verbose', '--no-hostonly',
                    '--no-hostonly-cmdline',
                    '--add', ' foo ', '--omit', ' bar ',
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
