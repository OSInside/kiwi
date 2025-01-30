import logging
import os
from pytest import (
    raises, fixture
)
from unittest.mock import (
    patch, call, Mock, MagicMock, ANY
)

from kiwi.exceptions import (
    KiwiBootStrapPhaseFailed,
    KiwiSystemUpdateFailed,
    KiwiSystemInstallPackagesFailed,
    KiwiSystemDeletePackagesFailed,
    KiwiInstallPhaseFailed,
    KiwiPackagesDeletePhaseFailed
)

from kiwi.defaults import Defaults
from kiwi.system.prepare import SystemPrepare
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState


class TestSystemPrepare:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.system.prepare.RootInit')
    @patch('kiwi.system.prepare.RootBind')
    @patch('kiwi.logger.Logger.get_logfile')
    def setup(self, mock_get_logfile, mock_root_bind, mock_root_init):
        Defaults.set_platform_name('x86_64')
        mock_get_logfile.return_value = None
        description = XMLDescription(
            description='../data/example_config.xml',
            derived_from='derived/description'
        )
        self.description_dir = os.path.dirname(description.description_origin)
        self.xml = description.load()

        self.manager = MagicMock(
            return_value=MagicMock()
        )
        self.manager.package_requests = ['foo']
        self.manager.collection_requests = ['foo']
        self.manager.product_requests = ['foo']

        root_init = MagicMock()
        mock_root_init.return_value = root_init
        root_bind = MagicMock()
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
        root_bind.mount_kernel_file_systems.assert_called_once_with(None)

    @patch('kiwi.system.prepare.RootInit')
    @patch('kiwi.system.prepare.RootBind')
    @patch('kiwi.logger.Logger.get_logfile')
    def setup_method(self, cls, mock_get_logfile, mock_root_bind, mock_root_init):
        self.setup()

    @patch('kiwi.system.prepare.RootImport.new')
    @patch('kiwi.system.prepare.RootInit')
    @patch('kiwi.system.prepare.RootBind')
    @patch('kiwi.logger.Logger.get_logfile')
    def test_init_with_derived_from_image(
        self, mock_get_logfile, mock_root_bind, mock_root_init, mock_root_import
    ):
        mock_get_logfile.return_value = 'logfile'
        description = XMLDescription(
            description='../data/example_config.xml',
            derived_from='derived/description'
        )
        xml = description.load()

        root_init = MagicMock()
        mock_root_init.return_value = root_init
        root_import = Mock()
        root_import.sync_data = Mock()
        mock_root_import.return_value = root_import
        root_bind = MagicMock()
        root_bind.root_dir = 'root_dir'
        mock_root_bind.return_value = root_bind
        state = XMLState(
            xml, profiles=['containerFlavour'], build_type='docker'
        )
        uri = Mock()
        get_derived_from_image_uri = Mock(
            return_value=uri
        )
        state.get_derived_from_image_uri = get_derived_from_image_uri
        system = SystemPrepare(
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
        root_bind.mount_kernel_file_systems.assert_called_once_with(None)
        assert system.issue_message == '{headline}: {reason}'

    @patch('kiwi.system.prepare.RootImport.new')
    @patch('kiwi.system.prepare.RootInit')
    @patch('kiwi.system.prepare.RootBind')
    @patch('kiwi.logger.Logger.get_logfile')
    def test_init_with_derived_from_image_for_delta_root(
        self, mock_get_logfile, mock_root_bind, mock_root_init, mock_root_import
    ):
        mock_get_logfile.return_value = 'logfile'
        description = XMLDescription(
            description='../data/example_config.xml',
            derived_from='derived/description'
        )
        xml = description.load()

        root_init = MagicMock()
        mock_root_init.return_value = root_init
        root_import = Mock()
        root_import.overlay_data = Mock()

        mock_root_import.return_value = root_import
        root_bind = MagicMock()
        root_bind.root_dir = 'root_dir'
        mock_root_bind.return_value = root_bind
        state = XMLState(
            xml, profiles=['containerFlavour'], build_type='docker'
        )
        uri = Mock()
        get_derived_from_image_uri = Mock(
            return_value=uri
        )
        get_delta_root = Mock(
            return_value=True
        )
        state.get_derived_from_image_uri = get_derived_from_image_uri
        state.build_type.get_delta_root = get_delta_root
        system = SystemPrepare(
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
        root_import.overlay_data.assert_called_once_with()
        mock_root_bind.assert_called_once_with(
            root_init
        )
        root_bind.setup_intermediate_config.assert_called_once_with()
        root_bind.mount_kernel_file_systems.assert_called_once_with(True)
        assert system.issue_message == '{headline}: {reason}'

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_install_bootstrap_packages_raises(self, mock_poll):
        self.manager.get_error_details.return_value = 'error-details'
        mock_poll.side_effect = Exception('some_error')
        with raises(KiwiBootStrapPhaseFailed) as issue:
            self.system.install_bootstrap(self.manager)
        assert issue.value.message == self.system.issue_message.format(
            headline='Bootstrap package installation failed',
            reason='some_error: error-details'
        )

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.ArchiveTar')
    def test_install_bootstrap_archives_raises(
        self, mock_tar, mock_poll
    ):
        mock_tar.side_effect = Exception
        with raises(KiwiBootStrapPhaseFailed):
            self.system.install_bootstrap(self.manager)

    @patch('kiwi.system.prepare.CommandProcess.poll')
    def test_update_system_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        with raises(KiwiSystemUpdateFailed):
            self.system.update_system(self.manager)

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_install_packages_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        with raises(KiwiSystemInstallPackagesFailed):
            self.system.install_packages(self.manager, ['package'])

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_install_system_packages_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        with raises(KiwiInstallPhaseFailed):
            self.system.install_system(self.manager)

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.ArchiveTar')
    def test_install_system_archives_raises(
        self, mock_tar, mock_poll
    ):
        mock_tar.side_effect = KiwiInstallPhaseFailed
        with raises(KiwiInstallPhaseFailed):
            self.system.install_system(self.manager)

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_delete_packages_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        with raises(KiwiSystemDeletePackagesFailed):
            self.system.delete_packages(self.manager, ['package'])

    @patch('kiwi.system.prepare.Repository.new')
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
        uri = Mock()
        mock_uri.return_value = uri
        self.system.root_bind = Mock()
        uri.is_remote = Mock(
            return_value=False
        )
        uri.translate = Mock(
            return_value='uri'
        )
        uri.alias = Mock(
            return_value='uri-alias'
        )
        uri.credentials_file_name = Mock(
            return_value='credentials-file'
        )
        repo = Mock()
        mock_repo.return_value.__enter__.return_value = repo

        self.system.setup_repositories(
            clear_cache=True,
            signing_keys=['key-file-a.asc', 'key-file-b.asc'],
            target_arch='x86_64'
        )

        mock_repo.assert_called_once_with(
            self.system.root_bind, 'package-manager-name', [
                'check_signatures', 'exclude_docs',
                '_install_langs%POSIX:C:C.UTF-8:en_US:de_DE',
                '_target_arch%x86_64'
            ]
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
                'uri-alias', 'uri', None, 42,
                None, None, None, None, 'credentials-file', None, None,
                'baseurl', None, None
            ),
            call(
                'uri-alias', 'uri', 'rpm-md', None,
                None, None, None, None, 'credentials-file', None, None,
                None, '../data/script', None
            )
        ]
        assert repo.delete_repo_cache.call_args_list == [
            call('uri-alias'),
            call('uri-alias')
        ]
        repo.setup_package_database_configuration.assert_called_once_with()
        repo.import_trusted_keys.assert_called_once_with(
            ['key-file-a.asc', 'key-file-b.asc']
        )

    @patch('kiwi.system.prepare.Repository.new')
    @patch('kiwi.system.prepare.Uri')
    @patch('kiwi.system.prepare.PackageManager')
    @patch('kiwi.xml_state.XMLState.get_package_manager')
    @patch('os.path.exists')
    def test_setup_repositories_local_not_existing(
        self, mock_exists, mock_package_manager,
        mock_manager, mock_uri, mock_repo
    ):
        mock_exists.return_value = False
        mock_package_manager.return_value = 'package-manager-name'
        uri = Mock()
        mock_uri.return_value = uri
        self.system.root_bind = Mock()
        uri.is_remote = Mock(
            return_value=False
        )
        uri.translate = Mock(
            return_value='uri'
        )
        uri.alias = Mock(
            return_value='uri-alias'
        )
        repo = Mock()
        mock_repo.return_value.__enter__.return_value = repo
        with self._caplog.at_level(logging.WARNING):
            self.system.setup_repositories()

    @patch('kiwi.xml_state.XMLState.get_bootstrap_collection_type')
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.ArchiveTar')
    @patch('os.path.exists')
    def test_install_bootstrap(
        self, mock_exists, mock_tar, mock_poll, mock_collection_type
    ):
        mock_exists.return_value = True
        tar = Mock()
        tar.extract = Mock()
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
        self.manager.setup_repository_modules.assert_called_once_with(
            {'disable': ['mod_c'], 'enable': ['mod_a:stream', 'mod_b']}
        )
        self.manager.process_install_requests_bootstrap.assert_called_once_with(
            self.system.root_bind, None
        )
        mock_tar.assert_called_once_with(
            '{0}/bootstrap.tgz'.format(self.description_dir)
        )
        tar.extract.assert_called_once_with('root_dir')
        self.manager.post_process_install_requests_bootstrap.assert_called_once_with(
            self.system.root_bind, None
        )

    @patch('kiwi.system.prepare.RootInit')
    @patch('kiwi.system.prepare.RootBind')
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.ArchiveTar')
    def test_install_bootstrap_archive_target_dir(
        self, mock_tar, mock_poll, mock_root_bind, mock_root_init
    ):
        Defaults.set_platform_name('x86_64')
        description = XMLDescription(
            description='../data/example_config_target_dir.xml'
        )
        self.xml = description.load()
        root_bind = MagicMock()
        root_bind.root_dir = 'root_dir'
        mock_root_bind.return_value = root_bind
        self.state = XMLState(
            self.xml
        )
        self.system = SystemPrepare(
            xml_state=self.state, root_dir='root_dir',
            allow_existing=True
        )
        tar = Mock()
        mock_tar.return_value = tar

        self.system.install_bootstrap(self.manager)

        assert tar.extract.call_args_list == [
            call('root_dir/foo'),
            call('root_dir/etc')
        ]

    @patch('kiwi.xml_state.XMLState.get_bootstrap_packages_sections')
    def test_install_bootstrap_skipped(self, mock_bootstrap_section):
        mock_bootstrap_section.return_value = []
        self.system.install_bootstrap(self.manager)
        with self._caplog.at_level(logging.WARNING):
            mock_bootstrap_section.assert_called_once_with()

    @patch('kiwi.xml_state.XMLState.get_bootstrap_collection_type')
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.ArchiveTar')
    @patch('os.path.exists')
    def test_install_bootstrap_archive_from_derived_description(
        self, mock_exists, mock_tar, mock_poll,
        mock_collection_type
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
        tar = Mock()
        tar.extract = Mock()
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
        self.manager.post_process_delete_requests.assert_has_calls(
            [call(self.system.root_bind), call(self.system.root_bind)]
        )

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    @patch('kiwi.system.prepare.Command.run')
    def test_pinch_system_in_delta_root_mode(self, mock_Command_run, mock_poll):
        self.system.delta_root = True
        self.system.pinch_system(self.manager)
        mock_Command_run.assert_called_once_with(
            ['rsync', '-a', 'root_dir_cow/', 'root_dir_cow_before_pinch']
        )

    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_pinch_system_raises(self, mock_poll):
        mock_poll.side_effect = Exception
        with raises(KiwiPackagesDeletePhaseFailed):
            self.system.pinch_system(self.manager)
        self.manager.process_delete_requests.assert_called_once_with(False)

    @patch('kiwi.package_manager.zypper.PackageManagerZypper.process_delete_requests')
    @patch('kiwi.system.prepare.Repository.new')
    @patch('kiwi.system.prepare.CommandProcess.poll_show_progress')
    def test_pinch_system_without_manager(
        self, mock_poll, mock_repo, mock_requests
    ):
        self.system.pinch_system()
        mock_repo.assert_called_once_with(ANY, 'zypper')
        mock_requests.assert_called_once_with(False)

    @patch('kiwi.system.prepare.CommandProcess.poll')
    def test_update_system(self, mock_poll):
        self.system.update_system(self.manager)
        self.manager.update.assert_called_once_with()

    @patch('kiwi.system.prepare.RootBind')
    @patch('kiwi.system.prepare.RootInit')
    @patch('kiwi.logger.Logger.get_logfile')
    def test_context_manager_exit(
        self, mock_get_logfile, mock_RootInit, mock_RootBind
    ):
        root_bind = Mock()
        mock_RootBind.return_value = root_bind
        root_import = Mock()
        with SystemPrepare(
            xml_state=self.state, root_dir='root_dir', allow_existing=True
        ) as system:
            system.root_import = root_import
        root_bind.cleanup.assert_called_once_with()
        root_import.overlay_finalize.assert_called_once_with(self.state)

    @patch('kiwi.system.prepare.Repository.new')
    @patch('kiwi.system.prepare.PackageManager.new')
    def test_clean_package_manager_leftovers(self, mock_manager, mock_repo):
        manager = Mock()
        mock_manager.return_value.__enter__.return_value = manager
        self.system.clean_package_manager_leftovers()
        manager.clean_leftovers.assert_called_once_with()
