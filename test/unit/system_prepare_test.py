from mock import patch
from mock import call
import mock

from .test_helper import raises

from kiwi.exceptions import (
    KiwiBootStrapPhaseFailed,
    KiwiSystemUpdateFailed,
    KiwiSystemInstallPackagesFailed,
    KiwiSystemDeletePackagesFailed,
    KiwiInstallPhaseFailed,
    KiwiPackagesDeletePhaseFailed
)

from kiwi.system.prepare import SystemPrepare
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState


class TestSystemPrepare(object):
    @patch('kiwi.system.prepare.RootInit')
    @patch('kiwi.system.prepare.RootBind')
    def setup(self, mock_root_bind, mock_root_init):
        description = XMLDescription(
            description='../data/example_config.xml',
            derived_from='derived/description'
        )
        self.xml = description.load()

        self.manager = mock.MagicMock(
            return_value=mock.MagicMock()
        )
        self.manager.package_requests = ['foo']
        self.manager.collection_requests = ['foo']
        self.manager.product_requests = ['foo']

        root_init = mock.MagicMock()
        mock_root_init.return_value = root_init
        root_bind = mock.MagicMock()
        root_bind.root_dir = 'root_dir'
        mock_root_bind.return_value = root_bind
        self.state = XMLState(
            self.xml
        )
        self.system = SystemPrepare(
            xml_state=self.state, root_dir='root_dir',
            allow_existing=True
        )
        mock_root_init.assert_called_once_with(
            'root_dir', True
        )
        root_init.create.assert_called_once_with()
        mock_root_bind.assert_called_once_with(
            root_init
        )
        root_bind.setup_intermediate_config.assert_called_once_with()
        root_bind.mount_kernel_file_systems.assert_called_once_with()

    @patch('kiwi.system.prepare.RootImport')
    @patch('kiwi.system.prepare.RootInit')
    @patch('kiwi.system.prepare.RootBind')
    def test_init_with_derived_from_image(
        self, mock_root_bind, mock_root_init, mock_root_import
    ):
        description = XMLDescription(
            description='../data/example_config.xml',
            derived_from='derived/description'
        )
        xml = description.load()

        root_init = mock.MagicMock()
        mock_root_init.return_value = root_init
        root_import = mock.Mock()
        root_import.sync_data = mock.Mock()
        mock_root_import.return_value = root_import
        root_bind = mock.MagicMock()
        root_bind.root_dir = 'root_dir'
        mock_root_bind.return_value = root_bind
        state = XMLState(
            xml, profiles=['vmxFlavour'], build_type='docker'
        )
        uri = mock.Mock()
        get_derived_from_image_uri = mock.Mock(
            return_value=uri
        )
        state.get_derived_from_image_uri = get_derived_from_image_uri
        SystemPrepare(
            xml_state=state, root_dir='root_dir',
        )
        mock_root_init.assert_called_once_with(
            'root_dir', False
        )
        root_init.create.assert_called_once_with()
        mock_root_import.assert_called_once_with(
            'root_dir', uri,
            state.build_type.get_image()
        )
        root_import.sync_data.assert_called_once_with()
        mock_root_bind.assert_called_once_with(
            root_init
        )
        root_bind.setup_intermediate_config.assert_called_once_with()
        root_bind.mount_kernel_file_systems.assert_called_once_with()

    @raises(KiwiBootStrapPhaseFailed)
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_install_bootstrap_packages_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        self.system.install_bootstrap(self.manager)

    @raises(KiwiBootStrapPhaseFailed)
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.ArchiveTar')
    def test_install_bootstrap_archives_raises(self, mock_tar, mock_poll):
        mock_tar.side_effect = Exception
        self.system.install_bootstrap(self.manager)

    @raises(KiwiSystemUpdateFailed)
    @patch('kiwi.system.prepare.CommandProcess.poll')
    def test_update_system_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        self.system.update_system(self.manager)

    @raises(KiwiSystemInstallPackagesFailed)
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_install_packages_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        self.system.install_packages(self.manager, ['package'])

    @raises(KiwiInstallPhaseFailed)
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_install_system_packages_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        self.system.install_system(self.manager)

    @raises(KiwiInstallPhaseFailed)
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.ArchiveTar')
    def test_install_system_archives_raises(self, mock_tar, mock_poll):
        mock_tar.side_effect = KiwiInstallPhaseFailed
        self.system.install_system(self.manager)

    @raises(KiwiSystemDeletePackagesFailed)
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_delete_packages_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        self.system.delete_packages(self.manager, ['package'])

    @patch('kiwi.system.prepare.Repository')
    @patch('kiwi.system.prepare.Uri')
    @patch('kiwi.system.prepare.PackageManager')
    @patch('kiwi.xml_state.XMLState.get_package_manager')
    @patch('os.path.exists')
    def test_setup_repositories(
        self, mock_exists, mock_package_manager,
        mock_manager, mock_uri, mock_repo
    ):
        mock_exists.return_value = True
        mock_package_manager.return_value = 'package-manager-name'
        uri = mock.Mock()
        mock_uri.return_value = uri
        self.system.root_bind = mock.Mock()
        uri.is_remote = mock.Mock(
            return_value=False
        )
        uri.translate = mock.Mock(
            return_value='uri'
        )
        uri.alias = mock.Mock(
            return_value='uri-alias'
        )
        uri.credentials_file_name = mock.Mock(
            return_value='credentials-file'
        )
        repo = mock.Mock()
        mock_repo.return_value = repo

        self.system.setup_repositories(
            clear_cache=True,
            signing_keys=['key-file-a.asc', 'key-file-b.asc']
        )

        mock_repo.assert_called_once_with(
            self.system.root_bind, 'package-manager-name',
            ['check_signatures', 'exclude_docs']
        )
        # mock local repos will be translated and bind mounted
        assert uri.translate.call_args_list == [
            call(), call()
        ]
        assert self.system.root_bind.mount_shared_directory.call_args_list == [
            call('uri'), call('uri')
        ]
        assert uri.alias.call_args_list == [
            call(), call()
        ]
        assert repo.add_repo.call_args_list == [
            call(
                'uri-alias', 'uri', 'yast2', 42,
                None, None, None, None, 'credentials-file', None, None
            ),
            call(
                'uri-alias', 'uri', 'rpm-md', None,
                None, None, None, None, 'credentials-file', None, None
            )
        ]
        assert repo.delete_repo_cache.call_args_list == [
            call('uri-alias'),
            call('uri-alias')
        ]
        repo.import_trusted_keys.assert_called_once_with(
            ['key-file-a.asc', 'key-file-b.asc']
        )

    @patch('kiwi.system.prepare.Repository')
    @patch('kiwi.system.prepare.Uri')
    @patch('kiwi.system.prepare.PackageManager')
    @patch('kiwi.xml_state.XMLState.get_package_manager')
    @patch('os.path.exists')
    @patch('kiwi.logger.log.warning')
    def test_setup_repositories_local_not_existing(
        self, mock_log_warn, mock_exists, mock_package_manager,
        mock_manager, mock_uri, mock_repo
    ):
        mock_exists.return_value = False
        mock_package_manager.return_value = 'package-manager-name'
        uri = mock.Mock()
        mock_uri.return_value = uri
        self.system.root_bind = mock.Mock()
        uri.is_remote = mock.Mock(
            return_value=False
        )
        uri.translate = mock.Mock(
            return_value='uri'
        )
        uri.alias = mock.Mock(
            return_value='uri-alias'
        )
        repo = mock.Mock()
        mock_repo.return_value = repo
        self.system.setup_repositories()
        assert mock_log_warn.called

    @patch('kiwi.xml_state.XMLState.get_bootstrap_collection_type')
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.ArchiveTar')
    @patch('os.path.exists')
    def test_install_bootstrap(
        self, mock_exists, mock_tar, mock_poll, mock_collection_type
    ):
        mock_exists.return_value = True
        tar = mock.Mock()
        tar.extract = mock.Mock()
        mock_tar.return_value = tar
        mock_collection_type.return_value = 'onlyRequired'
        self.system.install_bootstrap(self.manager)
        self.manager.process_only_required.assert_called_once_with()
        self.manager.request_package.assert_any_call(
            'filesystem'
        )
        self.manager.request_package.assert_any_call(
            'zypper'
        )
        self.manager.request_collection.assert_called_once_with(
            'bootstrap-collection'
        )
        self.manager.request_product.assert_called_once_with(
            'kiwi'
        )
        self.manager.process_install_requests_bootstrap.assert_called_once_with(
        )
        mock_tar.assert_called_once_with('../data/bootstrap.tgz')
        tar.extract.assert_called_once_with('root_dir')

    @patch('kiwi.logger.log.warning')
    @patch('kiwi.xml_state.XMLState.get_bootstrap_packages_sections')
    def test_install_bootstrap_skipped(
        self, mock_bootstrap_section, mock_log_warning
    ):
        mock_bootstrap_section.return_value = []
        self.system.install_bootstrap(self.manager)
        mock_bootstrap_section.assert_called_once_with()
        assert mock_log_warning.called

    @patch('kiwi.xml_state.XMLState.get_bootstrap_collection_type')
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.ArchiveTar')
    @patch('os.path.exists')
    def test_install_bootstrap_archive_from_derived_description(
        self, mock_exists, mock_tar, mock_poll, mock_collection_type
    ):
        mock_exists.return_value = False
        self.system.install_bootstrap(self.manager)
        mock_tar.assert_called_once_with(
            'derived/description/bootstrap.tgz'
        )

    @patch('kiwi.xml_state.XMLState.get_system_collection_type')
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.ArchiveTar')
    @patch('os.path.exists')
    def test_install_system(
        self, mock_exists, mock_tar, mock_poll, mock_collection_type
    ):
        mock_exists.return_value = True
        tar = mock.Mock()
        tar.extract = mock.Mock()
        mock_tar.return_value = tar
        mock_collection_type.return_value = 'onlyRequired'
        self.system.install_system(self.manager)
        self.manager.process_only_required.assert_called_once_with()
        self.manager.request_package.assert_any_call(
            'plymouth-branding-openSUSE'
        )
        self.manager.request_collection.assert_any_call(
            'base'
        )
        self.manager.request_product.assert_any_call(
            'openSUSE'
        )
        self.manager.request_package_exclusion.assert_any_call(
            'foo'
        )
        self.manager.process_install_requests.assert_called_once_with()
        mock_tar.assert_called_once_with('/absolute/path/to/image.tgz')
        tar.extract.assert_called_once_with('root_dir')

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_install_packages(self, mock_poll):
        self.system.install_packages(self.manager, ['foo'])
        self.manager.request_package.assert_called_once_with('foo')

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_delete_packages(self, mock_poll):
        self.system.delete_packages(self.manager, ['foo'])
        self.manager.request_package.assert_called_once_with('foo')

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_pinch_system(self, mock_poll):
        self.system.pinch_system(self.manager, force=False)
        self.system.pinch_system(self.manager, force=True)
        self.manager.process_delete_requests.assert_has_calls(
            [call(False), call(True)]
        )

    @raises(KiwiPackagesDeletePhaseFailed)
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_pinch_system_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        self.system.pinch_system(self.manager)
        self.manager.process_delete_requests.assert_called_once_with()

    @patch('kiwi.package_manager.PackageManagerZypper.process_delete_requests')
    @patch('kiwi.system.prepare.Repository')
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_pinch_system_without_manager(
        self, mock_poll, mock_repo, mock_requests
    ):
        self.system.pinch_system()
        mock_repo.assert_called_once_with(mock.ANY, 'zypper')
        mock_requests.assert_called_once_with(False)

    @patch('kiwi.system.prepare.CommandProcess.poll')
    def test_update_system(self, mock_poll):
        self.system.update_system(self.manager)
        self.manager.update.assert_called_once_with()

    def test_destructor(self):
        self.system.__del__()
        self.system.root_bind.cleanup.assert_called_once_with()

    def test_destructor_raising(self):
        self.system.root_bind = mock.Mock()
        self.system.root_bind.cleanup.side_effect = Exception
        del self.system
