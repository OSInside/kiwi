from mock import (
    patch, call, mock_open
)
from pytest import raises
import mock
import kiwi

from kiwi.system.uri import Uri
from kiwi.builder.container import ContainerBuilder
from kiwi.exceptions import KiwiContainerBuilderError


class TestContainerBuilder:
    @patch('platform.machine')
    @patch('os.path.exists')
    def setup(self, mock_exists, mock_machine):
        mock_machine.return_value = 'x86_64'
        with patch.dict('os.environ', {'HOME': '../data'}):
            self.uri = Uri('file:///image_file.tar.xz')
        self.xml_state = mock.Mock()
        self.xml_state.get_derived_from_image_uri.return_value = self.uri
        self.container_config = {
            'container_name': 'my-container',
            'entry_command': ["--config.cmd='/bin/bash'"]
        }
        self.xml_state.get_container_config = mock.Mock(
            return_value=self.container_config
        )
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='docker'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='image_name'
        )
        self.setup = mock.Mock()
        kiwi.builder.container.SystemSetup = mock.Mock(
            return_value=self.setup
        )

        def side_effect(filename):
            if filename.endswith('.config/kiwi/config.yml'):
                return False
            elif filename.endswith('etc/kiwi.yml'):
                return False
            else:
                return True

        mock_exists.side_effect = side_effect

        self.container = ContainerBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        self.container.result = mock.Mock()

    def test_init_derived(self):
        assert self.container.base_image == 'root_dir/image/imported_root'

    @patch('os.path.exists')
    def test_init_derived_base_image_not_existing(self, mock_exists):
        mock_exists.return_value = False
        with raises(KiwiContainerBuilderError):
            ContainerBuilder(
                self.xml_state, 'target_dir', 'root_dir'
            )

    @patch('os.path.exists')
    def test_init_derived_base_image_md5_not_existing(self, mock_exists):
        exists_results = [False, False, True]

        def side_effect(self):
            return exists_results.pop()

        mock_exists.side_effect = side_effect
        with raises(KiwiContainerBuilderError):
            ContainerBuilder(
                self.xml_state, 'target_dir', 'root_dir'
            )

    @patch('kiwi.builder.container.Checksum')
    @patch('kiwi.builder.container.ContainerImage')
    @patch('os.path.exists')
    def test_create_derived_checksum_match_failed(
        self, mock_exists, mock_image, mock_checksum
    ):
        def side_effect(filename):
            if filename.endswith('.config/kiwi/config.yml'):
                return False
            elif filename.endswith('etc/kiwi.yml'):
                return False
            else:
                return True

        mock_exists.side_effect = side_effect

        container = ContainerBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        container.result = mock.Mock()

        checksum = mock.Mock()
        checksum.matches = mock.Mock(
            return_value=False
        )
        mock_checksum.return_value = checksum
        with raises(KiwiContainerBuilderError):
            container.create()

    @patch('kiwi.builder.container.ContainerSetup')
    @patch('kiwi.builder.container.ContainerImage')
    def test_create(self, mock_image, mock_setup):
        container_setup = mock.Mock()
        mock_setup.return_value = container_setup
        container_image = mock.Mock()
        container_image.create = mock.Mock(
            return_value='target_dir/image_name.x86_64-1.2.3.docker.tar.xz'
        )
        mock_image.return_value = container_image
        self.setup.export_package_verification.return_value = '.verified'
        self.setup.export_package_list.return_value = '.packages'
        self.container.base_image = None
        self.container.create()
        mock_setup.assert_called_once_with(
            'docker', 'root_dir', self.container_config
        )
        container_setup.setup.assert_called_once_with()
        mock_image.assert_called_once_with(
            'docker', 'root_dir', self.container_config
        )
        container_image.create.assert_called_once_with(
            'target_dir/image_name.x86_64-1.2.3.docker.tar', None
        )
        assert self.container.result.add.call_args_list == [
            call(
                key='container',
                filename='target_dir/image_name.x86_64-1.2.3.docker.tar.xz',
                use_for_bundle=True,
                compress=False,
                shasum=True
            ),
            call(
                key='image_packages',
                filename='.packages',
                use_for_bundle=True,
                compress=False,
                shasum=False
            ),
            call(
                key='image_verified',
                filename='.verified',
                use_for_bundle=True,
                compress=False,
                shasum=False
            )
        ]
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )

    @patch('kiwi.builder.container.Checksum')
    @patch('kiwi.builder.container.ContainerImage')
    @patch('os.path.exists')
    def test_create_derived(self, mock_exists, mock_image, mock_checksum):
        def side_effect(filename):
            if filename.endswith('.config/kiwi/config.yml'):
                return False
            elif filename.endswith('etc/kiwi.yml'):
                return False
            else:
                return True

        mock_exists.side_effect = side_effect

        container_image = mock.Mock()
        container_image.create = mock.Mock(
            return_value='target_dir/image_name.x86_64-1.2.3.docker.tar.xz'
        )
        mock_image.return_value = container_image

        container = ContainerBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        container.result = mock.Mock()

        checksum = mock.Mock()
        checksum.md5 = mock.Mock(
            return_value='checksumvalue'
        )
        mock_checksum.return_value = checksum

        self.setup.export_package_verification.return_value = '.verified'
        self.setup.export_package_list.return_value = '.packages'

        container.create()

        mock_checksum.assert_called_once_with('root_dir/image/imported_root')
        checksum.matches.assert_called_once_with(
            'checksumvalue', 'root_dir/image/imported_root.md5'
        )

        mock_image.assert_called_once_with(
            'docker', 'root_dir', self.container_config
        )
        container_image.create.assert_called_once_with(
            'target_dir/image_name.x86_64-1.2.3.docker.tar',
            'root_dir/image/imported_root'
        )
        assert container.result.add.call_args_list == [
            call(
                key='container',
                filename='target_dir/image_name.x86_64-1.2.3.docker.tar.xz',
                use_for_bundle=True,
                compress=False,
                shasum=True
            ),
            call(
                key='image_packages',
                filename='.packages',
                use_for_bundle=True,
                compress=False,
                shasum=False
            ),
            call(
                key='image_verified',
                filename='.verified',
                use_for_bundle=True,
                compress=False,
                shasum=False
            )
        ]
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )

    @patch('kiwi.builder.container.Checksum')
    def test_create_derived_with_different_md5(self, mock_md5):
        md5 = mock.Mock()
        md5.md5.return_value = 'diffchecksumvalue'
        mock_md5.return_value = md5

        m_open = mock_open(read_data='checksum data\n')
        with patch('builtins.open', m_open, create=True):
            with raises(KiwiContainerBuilderError):
                container = ContainerBuilder(
                    self.xml_state, 'target_dir', 'root_dir'
                )
                container.create()

    @patch('kiwi.builder.container.Checksum')
    def test_create_derived_fail_open(self, mock_md5):
        with patch('builtins.open') as m_open:
            m_open = mock_open()
            m_open.return_value.__enter__.side_effect = Exception(
                'open failed'
            )
            with raises(Exception) as e:
                container = ContainerBuilder(
                    self.xml_state, 'target_dir', 'root_dir'
                )
                container.create()
                assert 'open failed' in str(e)
