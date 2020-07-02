from mock import (
    patch, call, Mock
)
from collections import namedtuple

from kiwi.boot.image.dracut import BootImageDracut
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState


class TestBootImageKiwi:
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.base.os.path.exists')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_exists, mock_cmd):
        mock_machine.return_value = 'x86_64'
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
        assert self.boot_image.included_files_install == []

    def test_include_module(self):
        self.boot_image.include_module('foobar')
        assert self.boot_image.modules == ['foobar']
        assert self.boot_image.install_modules == []

        self.boot_image.include_module('module', install_media=True)
        self.boot_image.include_module('foobar')
        self.boot_image.include_module('not_available')
        assert self.boot_image.modules == ['foobar']
        assert self.boot_image.install_modules == ['module']

    def test_omit_module(self):
        self.boot_image.omit_module('foobar')
        assert self.boot_image.omit_modules == ['foobar']
        assert self.boot_image.omit_install_modules == []

        self.boot_image.omit_module('module', install_media=True)
        self.boot_image.omit_module('foobar')
        assert self.boot_image.omit_modules == ['foobar']
        assert self.boot_image.omit_install_modules == ['module']

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
        self.boot_image.include_file('foo', install_media=True)
        assert self.boot_image.included_files == [
            '--install', 'foo'
        ]
        assert self.boot_image.included_files_install == [
            '--install', 'foo'
        ]

    @patch('kiwi.boot.image.dracut.Kernel')
    @patch('kiwi.boot.image.dracut.Command.run')
    @patch('kiwi.boot.image.base.BootImageBase.is_prepared')
    @patch('kiwi.boot.image.dracut.Profile')
    def test_create_initrd(
        self, mock_Profile, mock_prepared, mock_command, mock_kernel
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
        self.boot_image.include_file(
            '/system-directory/var/lib/bar', install_media=True
        )
        self.boot_image.include_module('foo')
        self.boot_image.omit_module('bar')
        self.boot_image.create_initrd()
        profile.create.assert_called_once_with(
            'system-directory/.profile'
        )
        assert mock_command.call_args_list == [
            call([
                'chroot', 'system-directory',
                'dracut', '--verbose', '--no-hostonly',
                '--no-hostonly-cmdline', '--xz',
                '--add', ' foo ', '--omit', ' bar ',
                '--install', 'system-directory/etc/foo',
                '--install', '/system-directory/var/lib/bar',
                'LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd.xz', '1.2.3'
            ], stderr_to_stdout=True),
            call([
                'mv',
                'system-directory/'
                'LimeJeOS-openSUSE-13.2.x86_64-1.13.2.initrd.xz',
                'some-target-dir'
            ])
        ]
        mock_command.reset_mock()
        self.boot_image.create_initrd(basename='foo', install_initrd=True)
        assert mock_command.call_args_list == [
            call([
                'chroot', 'system-directory',
                'dracut', '--verbose', '--no-hostonly',
                '--no-hostonly-cmdline', '--xz',
                '--install', '/system-directory/var/lib/bar',
                'foo.xz', '1.2.3'
            ], stderr_to_stdout=True),
            call([
                'mv',
                'system-directory/foo.xz',
                'some-target-dir'
            ])
        ]
