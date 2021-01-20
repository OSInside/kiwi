from mock import patch

from kiwi.system.users import Users


class TestUsers:
    def setup(self):
        self.users = Users('root_dir')

    @patch('kiwi.system.users.Command.run')
    def test_user_exists(self, mock_command):
        assert self.users.user_exists('user') is True
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'grep', '-q', '^user:', '/etc/passwd']
        )

    @patch('kiwi.system.users.Command.run')
    def test_user_exists_return_value(self, mock_command):
        assert self.users.user_exists('user') is True
        mock_command.side_effect = Exception
        assert self.users.user_exists('user') is False

    @patch('kiwi.system.users.Command.run')
    def test_group_exists(self, mock_command):
        assert self.users.group_exists('group') is True
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'grep', '-q', '^group:', '/etc/group']
        )

    @patch('kiwi.system.users.Command.run')
    def test_group_add(self, mock_command):
        assert self.users.group_add('group', ['--option', 'value']) is None
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'groupadd', '--option', 'value', 'group']
        )

    @patch('kiwi.system.users.Command.run')
    def test_user_add(self, mock_command):
        assert self.users.user_add('user', ['--option', 'value']) is None
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'useradd', '--option', 'value', 'user']
        )

    @patch('kiwi.system.users.Command.run')
    def test_user_modify(self, mock_command):
        assert self.users.user_modify('user', ['--option', 'value']) is None
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'usermod', '--option', 'value', 'user']
        )

    @patch('kiwi.system.users.Command.run')
    def test_setup_home_for_user(self, mock_command):
        assert self.users.setup_home_for_user('user', 'group', '/home/path') \
            is None
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'chown', '-R', 'user:group', '/home/path']
        )
