from unittest.mock import patch

from kiwi.system.users import Users


class TestUsers:
    def setup(self):
        self.users = Users('root_dir')

    def setup_method(self, cls):
        self.setup()

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

    @patch('kiwi.system.users.Path.create')
    @patch('kiwi.system.users.Command.run')
    def test_user_add_creates_missing_home_parent(
        self, mock_command, mock_create
    ):
        assert self.users.user_add(
            'newuser', ['-m', '-d', '/path/to/home']
        ) is None
        mock_create.assert_called_once_with('root_dir/path/to')
        mock_command.assert_called_once_with(
            [
                'chroot', 'root_dir', 'useradd',
                '-m', '-d', '/path/to/home', 'newuser'
            ]
        )

    @patch('kiwi.system.users.Path.create')
    @patch('kiwi.system.users.Command.run')
    def test_user_add_skips_parent_for_top_level_home(self, mock_command, mock_create):
        self.users.user_add('newuser', ['-m', '-d', '/home'])
        mock_create.assert_not_called()
        mock_command.assert_called_once_with(
            ['chroot', 'root_dir', 'useradd', '-m', '-d', '/home', 'newuser']
        )

    @patch('kiwi.system.users.Path.create')
    @patch('kiwi.system.users.Command.run')
    def test_user_add_reads_home_from_equals_form(self, mock_command, mock_create):
        self.users.user_add('newuser', ['-m', '--home-dir=/path/to/home'])
        mock_create.assert_called_once_with('root_dir/path/to')
        mock_command.assert_called_once_with(
            [
                'chroot', 'root_dir', 'useradd',
                '-m', '--home-dir=/path/to/home', 'newuser'
            ]
        )

    @patch('kiwi.system.users.Path.create')
    @patch('kiwi.system.users.Command.run')
    def test_user_add_skips_relative_home(self, mock_command, mock_create):
        self.users.user_add('newuser', ['-m', '-d', 'relative/home'])
        mock_create.assert_not_called()

    @patch('os.path.isdir', return_value=True)
    @patch('kiwi.system.users.Path.create')
    @patch('kiwi.system.users.Command.run')
    def test_user_add_skips_existing_home_parent(
        self, mock_command, mock_create, mock_isdir
    ):
        self.users.user_add('newuser', ['-m', '--home', '/path/to/home'])
        mock_create.assert_not_called()
        mock_isdir.assert_called_once_with('root_dir/path/to')
