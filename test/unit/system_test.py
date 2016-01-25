from nose.tools import *
from mock import patch
from mock import call
import mock

import nose_helper

from kiwi.exceptions import (
    KiwiBootStrapPhaseFailed,
    KiwiSystemUpdateFailed,
    KiwiSystemInstallPackagesFailed,
    KiwiSystemDeletePackagesFailed,
    KiwiInstallPhaseFailed
)

import kiwi

from kiwi.system import System
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.command import Command


class FakeCommandCall(object):
    def __init__(self, returncode=0):
        self.process = self.__poll(returncode)
        self.data = self.__read()
        self.output = self.data
        self.error = self.data

    def output_available(self):
        return True

    def error_available(self):
        return True

    class __poll(object):
        def __init__(self, returncode):
            self.toggle_return_value = False
            self.returncode = returncode
            self.pid = 42

        def returncode(self):
            return self.returncode

        def poll(self):
            if not self.toggle_return_value:
                self.toggle_return_value = True
            else:
                return True

        def kill(self):
            pass

    class __read(object):
        def __init__(self):
            self.read_data = [
                '', '\n', 'o', 'o', 'f', ':', 'g', 'n', 'i', 'l',
                '', 'l', 'r', 'a', 'o', 't', 'r', 's', 'r', 'n', 'e', 'I'
            ]

        def read(self, byte):
            return self.read_data.pop()


class TestSystem(object):
    @patch('kiwi.system.RootInit')
    @patch('kiwi.system.RootBind')
    def setup(self, mock_root_bind, mock_root_init):
        description = XMLDescription('../data/example_config.xml')
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
        self.system = System(
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

    @raises(KiwiBootStrapPhaseFailed)
    def test_install_bootstrap_packages_raises(self):
        self.manager.process_install_requests_bootstrap = mock.Mock(
            return_value=FakeCommandCall(1)
        )
        self.system.install_bootstrap(self.manager)

    @raises(KiwiBootStrapPhaseFailed)
    @patch('kiwi.system.ArchiveTar')
    def test_install_bootstrap_archives_raises(self, mock_tar):
        mock_tar.side_effect = KiwiBootStrapPhaseFailed
        self.manager.process_install_requests_bootstrap = mock.Mock(
            return_value=FakeCommandCall(0)
        )
        self.system.install_bootstrap(self.manager)

    @raises(KiwiSystemUpdateFailed)
    def test_update_system_raises(self):
        self.manager.update = mock.Mock(
            return_value=FakeCommandCall(1)
        )
        self.system.update_system(self.manager)

    @raises(KiwiSystemInstallPackagesFailed)
    def test_install_packages_raises(self):
        self.manager.process_install_requests = mock.Mock(
            return_value=FakeCommandCall(1)
        )
        self.system.install_packages(self.manager, ['package'])

    @raises(KiwiInstallPhaseFailed)
    def test_install_system_packages_raises(self):
        self.manager.process_install_requests = mock.Mock(
            return_value=FakeCommandCall(1)
        )
        self.system.install_system(self.manager)

    @raises(KiwiInstallPhaseFailed)
    def test_pinch_system_raises(self):
        self.manager.process_install_requests = mock.Mock(
            return_value=FakeCommandCall(1)
        )
        self.system.pinch_system(self.manager)

    @raises(KiwiInstallPhaseFailed)
    def test_install_system_packages_delete_raises(self):
        self.manager.process_install_requests = mock.Mock(
            return_value=FakeCommandCall(0)
        )
        self.manager.process_delete_requests = mock.Mock(
            return_value=FakeCommandCall(1)
        )
        self.system.install_system(self.manager)

    @raises(KiwiInstallPhaseFailed)
    @patch('kiwi.system.ArchiveTar')
    def test_install_system_archives_raises(self, mock_tar):
        mock_tar.side_effect = KiwiInstallPhaseFailed
        self.manager.process_install_requests = mock.Mock(
            return_value=FakeCommandCall(0)
        )
        self.manager.process_delete_requests = mock.Mock(
            return_value=FakeCommandCall(0)
        )
        self.system.install_system(self.manager)

    @raises(KiwiSystemDeletePackagesFailed)
    def test_delete_packages_raises(self):
        self.manager.process_delete_requests = mock.Mock(
            return_value=FakeCommandCall(1)
        )
        self.system.delete_packages(self.manager, ['package'])

    @patch('kiwi.system.Repository')
    @patch('kiwi.system.Uri')
    @patch('kiwi.system.PackageManager')
    @patch('kiwi.xml_state.XMLState.get_package_manager')
    def test_setup_repositories(
        self, mock_package_manager, mock_manager, mock_uri, mock_repo
    ):
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

        mock_repo.assert_called_once_with(
            self.system.root_bind, 'package-manager-name'
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
            call('uri-alias', 'uri', 'yast2', 42),
            call('uri-alias', 'uri', 'rpm-md', None)
        ]

    @patch('kiwi.xml_state.XMLState.get_bootstrap_collection_type')
    @patch('kiwi.system.ArchiveTar')
    def test_install_bootstrap(self, mock_tar, mock_collection_type):
        tar = mock.Mock()
        tar.extract = mock.Mock()
        mock_tar.return_value = tar
        mock_collection_type.return_value = 'onlyRequired'
        self.manager.process_install_requests_bootstrap = mock.Mock(
            return_value=FakeCommandCall(0)
        )
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

    @patch('kiwi.xml_state.XMLState.get_system_collection_type')
    @patch('kiwi.system.ArchiveTar')
    def test_install_system(self, mock_tar, mock_collection_type):
        tar = mock.Mock()
        tar.extract = mock.Mock()
        mock_tar.return_value = tar
        mock_collection_type.return_value = 'onlyRequired'
        self.manager.process_install_requests = mock.Mock(
            return_value=FakeCommandCall(0)
        )
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
        self.manager.process_install_requests.assert_called_once_with()
        mock_tar.assert_called_once_with('../data/image.tgz')
        tar.extract.assert_called_once_with('root_dir')

    def test_pinch_system(self):
        self.manager.process_delete_requests = mock.Mock(
            return_value=FakeCommandCall(0)
        )
        self.system.pinch_system(self.manager)
        self.manager.request_package.assert_any_call(
            'kernel-debug'
        )
        self.manager.process_delete_requests.assert_called_once_with(False)

    def test_install_packages(self):
        self.manager.process_install_requests = mock.Mock(
            return_value=FakeCommandCall(0)
        )
        self.system.install_packages(self.manager, ['foo'])
        self.manager.request_package.assert_called_once_with('foo')

    def test_delete_packages(self):
        self.manager.process_delete_requests = mock.Mock(
            return_value=FakeCommandCall(0)
        )
        self.system.delete_packages(self.manager, ['foo'])
        self.manager.request_package.assert_called_once_with('foo')

    def test_update_system(self):
        self.manager.update = mock.Mock(
            return_value=FakeCommandCall(0)
        )
        self.system.update_system(self.manager)
        self.manager.update.assert_called_once_with()

    def test_destructor(self):
        self.system.__del__()
        self.system.root_bind.cleanup.assert_called_once_with()

    def test_destructor_raising(self):
        self.system.root_bind = mock.Mock()
        self.system.root_bind.cleanup.side_effect = Exception
        del self.system
