from unittest.mock import (
    patch, Mock, call
)

from kiwi.utils.rpm_database import RpmDataBase


class TestRpmDataBase:
    def setup(self):
        self.rpmdb = RpmDataBase('root_dir')
        self.rpmdb.rpmdb_host = Mock()
        self.rpmdb.rpmdb_image = Mock()

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.utils.rpm_database.Path.which')
    def test_has_rpm(self, mock_Path_which):
        mock_Path_which.return_value = None
        assert self.rpmdb.has_rpm() is False
        mock_Path_which.assert_called_once_with(
            'rpmdb', access_mode=1, root_dir='root_dir'
        )
        mock_Path_which.return_value = 'rpm'
        assert self.rpmdb.has_rpm() is True

    @patch('kiwi.command.Command.run')
    def test_rebuild_database(self, mock_Command_run):
        self.rpmdb.rebuild_database()
        mock_Command_run.assert_called_once_with(
            ['chroot', 'root_dir', 'rpmdb', '--rebuilddb']
        )

    @patch('kiwi.command.Command.run')
    def test_init_database(self, mock_Command_run):
        self.rpmdb.init_database()
        mock_Command_run.assert_called_once_with(
            ['rpm', '--root', 'root_dir', '--initdb']
        )

    def test_set_database_to_host_path(self):
        self.rpmdb.set_database_to_host_path()
        self.rpmdb.rpmdb_image.set_config_value.assert_called_once_with(
            '_dbpath', self.rpmdb.rpmdb_host.get_query.return_value
        )
        self.rpmdb.rpmdb_image.write_config.assert_called_once_with()
        self.rpmdb.rpmdb_host.get_query.assert_called_once_with('_dbpath')

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_link_database_to_host_path(self, mock_exists, mock_Command_run):
        self.rpmdb.rpmdb_image.expand_query.return_value = \
            '/var/lib/rpm'
        self.rpmdb.rpmdb_host.expand_query.return_value = \
            '/usr/lib/sysimage/rpm'
        mock_exists.return_value = False
        self.rpmdb.link_database_to_host_path()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'ln', '-s', '../../../var/lib/rpm',
                    'root_dir/usr/lib/sysimage/rpm'
                ]
            )
        ]

    @patch('kiwi.utils.rpm_database.Path.wipe')
    @patch('kiwi.command.Command.run')
    @patch('os.path.islink')
    @patch('os.path.exists')
    @patch('os.unlink')
    def test_set_database_to_image_path(
        self, mock_os_unlink, mock_os_exists, mock_os_islink,
        mock_Command_run, mock_Path_wipe
    ):
        mock_os_exists.return_value = True

        link = [False, False]

        def mocked_islink(path):
            return link.pop()

        mock_os_islink.side_effect = mocked_islink
        self.rpmdb.rpmdb_image.expand_query.return_value = \
            '/var/lib/rpm'
        self.rpmdb.rpmdb_host.expand_query.return_value = \
            '/usr/lib/sysimage/rpm'
        self.rpmdb.set_database_to_image_path()
        self.rpmdb.rpmdb_image.expand_query.assert_called_once_with('%_dbpath')
        assert self.rpmdb.rpmdb_image.set_config_value.call_args_list == [
            call(
                '_dbpath', self.rpmdb.rpmdb_host.expand_query.return_value
            ),
            call(
                '_dbpath_rebuild', self.rpmdb.rpmdb_image.get_query.return_value
            )
        ]
        assert mock_Path_wipe.call_args_list == [
            call('root_dir/var/lib/rpm'),
            call('root_dir/usr/lib/sysimage/rpm')
        ]
        self.rpmdb.rpmdb_image.write_config.assert_called_once_with()
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'chroot', 'root_dir', 'rpmdb', '--rebuilddb'
                ]
            ),
            call(
                [
                    'mv', 'root_dir/usr/lib/sysimage/rpm/alternatives',
                    'root_dir/var/lib/rpm'
                ]
            )
        ]
        assert self.rpmdb.rpmdb_image.wipe_config.call_count == 2
        link = [True, False]
        mock_os_islink.side_effect = mocked_islink
        self.rpmdb.set_database_to_image_path()
        mock_os_unlink.assert_called_once_with(
            'root_dir/var/lib/rpm'
        )
        link = [True, True]
        mock_os_islink.side_effect = mocked_islink
        self.rpmdb.set_database_to_image_path()
        assert mock_Command_run.call_args_list[-1] == call(
            ['chroot', 'root_dir', 'rpmdb', '--rebuilddb']
        )

    def test_set_macro_from_string(self):
        self.rpmdb.set_macro_from_string('_install_langs%en_US:de_DE')
        self.rpmdb.rpmdb_image.set_config_value.assert_called_once_with(
            '_install_langs', 'en_US:de_DE'
        )

    def test_write_config(self):
        self.rpmdb.write_config()
        self.rpmdb.rpmdb_image.write_config.assert_called_once_with()

    @patch('kiwi.command.Command.run')
    def test_import_signing_key_to_image(self, mock_Command_run):
        self.rpmdb.import_signing_key_to_image('key')
        mock_Command_run.assert_called_once_with(
            [
                'rpm', '--root', 'root_dir', '--import', 'key',
                '--dbpath', self.rpmdb.rpmdb_host.expand_query.return_value
            ]
        )
