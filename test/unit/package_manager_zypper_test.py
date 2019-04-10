from mock import patch
import mock

from .test_helper import raises

from kiwi.package_manager.zypper import PackageManagerZypper
from kiwi.exceptions import KiwiRequestError


class TestPackageManagerZypper(object):
    def setup(self):
        repository = mock.Mock()
        repository.root_dir = 'root-dir'

        root_bind = mock.Mock()
        root_bind.move_to_root = mock.Mock(
            return_value=['root-moved-arguments']
        )
        repository.root_bind = root_bind

        self.command_env = {
            'HOME': '/home/ms', 'ZYPP_CONF': 'root-dir/my/zypp.conf'
        }
        repository.runtime_config = mock.MagicMock(
            return_value={
                'zypper_args': ['--reposd-dir', 'root-dir/my/repos'],
                'command_env': self.command_env
            }
        )
        self.manager = PackageManagerZypper(repository)

        self.chroot_zypper_args = self.manager.root_bind.move_to_root(
            self.manager.zypper_args
        )
        self.chroot_command_env = self.manager.command_env
        zypp_conf = self.manager.command_env['ZYPP_CONF']
        self.chroot_command_env['ZYPP_CONF'] = \
            self.manager.root_bind.move_to_root(zypp_conf)[0]

    def test_request_package(self):
        self.manager.request_package('name')
        assert self.manager.package_requests == ['name']

    def test_request_collection(self):
        self.manager.request_collection('name')
        assert self.manager.collection_requests == ['pattern:name']

    def test_request_product(self):
        self.manager.request_product('name')
        assert self.manager.product_requests == ['product:name']

    def test_request_package_exclusion(self):
        self.manager.request_package_exclusion('name')
        assert self.manager.exclude_requests == ['name']

    @patch('kiwi.command.Command.call')
    def test_process_install_requests_bootstrap(self, mock_call):
        self.manager.request_package('vim')
        self.manager.process_install_requests_bootstrap()
        mock_call.assert_called_once_with(
            [
                'zypper', '--reposd-dir', 'root-dir/my/repos',
                '--root', 'root-dir',
                'install', '--auto-agree-with-licenses'
            ] + self.manager.custom_args + ['vim'], self.command_env
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    @patch('kiwi.package_manager.zypper.Path.create')
    def test_process_install_requests(
        self, mock_path, mock_exists, mock_run, mock_call
    ):
        mock_exists.return_value = False
        self.manager.request_package('vim')
        self.manager.request_package_exclusion('skipme')
        self.manager.process_install_requests()
        mock_path.assert_called_once_with('root-dir/etc/zypp')
        mock_run.assert_called_once_with(
            ['chroot', 'root-dir', 'zypper'] + self.chroot_zypper_args + [
                'al'
            ] + self.manager.custom_args + ['skipme'], self.chroot_command_env
        )
        mock_call.assert_called_once_with(
            ['chroot', 'root-dir', 'zypper'] + self.chroot_zypper_args + [
                'install', '--auto-agree-with-licenses'
            ] + self.manager.custom_args + ['vim'], self.chroot_command_env
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests_all_installed(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests()
        mock_call.assert_called_once_with(
            ['chroot', 'root-dir', 'zypper'] + self.chroot_zypper_args + [
                'remove', '-u', '--force-resolution'
            ] + self.manager.custom_args + ['vim'], self.chroot_command_env
        )

    @patch('kiwi.command.Command.call')
    @patch('kiwi.command.Command.run')
    def test_process_delete_requests_force(self, mock_run, mock_call):
        self.manager.request_package('vim')
        self.manager.process_delete_requests(True)
        mock_call.assert_called_once_with(
            [
                'chroot', 'root-dir', 'rpm', '-e',
                '--nodeps', '--allmatches', '--noscripts', 'vim'
            ], self.command_env
        )

    @patch('kiwi.command.Command.run')
    @patch('kiwi.command.Command.call')
    @raises(KiwiRequestError)
    def test_process_delete_requests_package_missing(self, mock_call, mock_run):
        mock_run.side_effect = Exception
        self.manager.request_package('vim')
        self.manager.process_delete_requests()
        mock_run.assert_called_once_with(
            ['chroot', 'root-dir', 'rpm', '-q', 'vim']
        )

    @patch('kiwi.command.Command.call')
    def test_update(self, mock_call):
        self.manager.update()
        mock_call.assert_called_once_with(
            ['chroot', 'root-dir', 'zypper'] + self.chroot_zypper_args + [
                'update', '--auto-agree-with-licenses'
            ] + self.manager.custom_args, self.chroot_command_env
        )

    def test_process_only_required(self):
        self.manager.process_only_required()
        assert self.manager.custom_args == ['--no-recommends']

    def test_process_plus_recommended(self):
        self.manager.process_only_required()
        assert self.manager.custom_args == ['--no-recommends']
        self.manager.process_plus_recommended()
        assert '--no-recommends' not in self.manager.custom_args

    def test_match_package_installed(self):
        assert self.manager.match_package_installed('foo', 'Installing: foo')

    def test_match_package_deleted(self):
        assert self.manager.match_package_deleted('foo', 'Removing: foo')

    @patch('kiwi.package_manager.zypper.RpmDataBase')
    def test_post_process_install_requests_bootstrap(self, mock_RpmDataBase):
        rpmdb = mock.Mock()
        rpmdb.has_rpm.return_value = True
        mock_RpmDataBase.return_value = rpmdb
        self.manager.post_process_install_requests_bootstrap()
        rpmdb.set_database_to_image_path.assert_called_once_with()

    def test_has_failed(self):
        assert self.manager.has_failed(0) is False
        assert self.manager.has_failed(102) is False
        assert self.manager.has_failed(100) is False
        assert self.manager.has_failed(104) is True
        assert self.manager.has_failed(105) is True
        assert self.manager.has_failed(106) is True
        assert self.manager.has_failed(1) is True
        assert self.manager.has_failed(4) is True
        assert self.manager.has_failed(-42) is True
