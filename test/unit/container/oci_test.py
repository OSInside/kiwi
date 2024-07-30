import logging
from pytest import fixture
from unittest.mock import (
    patch, mock_open, Mock
)

import kiwi

from kiwi.container.oci import ContainerImageOCI
from kiwi.version import __version__


class TestContainerImageOCI:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.defaults.Defaults.is_buildservice_worker')
    def setup(self, mock_is_buildservice_worker, mock_cmd_caps):
        mock_is_buildservice_worker.return_value = False
        mock_cmd_caps.return_value = True
        self.runtime_config = Mock()
        self.runtime_config.get_container_compression = Mock(
            return_value=None
        )
        kiwi.container.oci.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )
        self.oci = ContainerImageOCI(
            'root_dir', 'docker-archive', {
                'container_name': 'foo/bar',
                'additional_names': [':current', 'name:foobar', 'newname']
            }
        )

    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.defaults.Defaults.is_buildservice_worker')
    def setup_method(self, cls, mock_is_buildservice_worker, mock_cmd_caps):
        self.setup()

    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.defaults.Defaults.is_buildservice_worker')
    def test_init_custom_args(self, mock_is_buildservice_worker, mock_cmd_caps):
        mock_is_buildservice_worker.return_value = False
        mock_cmd_caps.return_value = True
        custom_args = {
            'container_name': 'foo',
            'container_tag': '1.0',
            'additional_names': ['current', 'foobar'],
            'entry_command': ['/bin/bash', '-x'],
            'entry_subcommand': ['ls', '-l'],
            'maintainer': 'tux',
            'user': 'root',
            'workingdir': '/root',
            'expose_ports': ['80', '42'],
            'volumes': ['/var/log', '/tmp'],
            'environment': {'PATH': '/bin', 'FOO': 'bar'},
            'labels': {'a': 'value', 'b': 'value'}
        }
        container = ContainerImageOCI(
            'root_dir', 'oci-archive', custom_args
        )
        assert container.oci_config == custom_args

    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.defaults.Defaults.is_buildservice_worker')
    def test_init_without_custom_args(
        self, mock_is_buildservice_worker, mock_cmd_caps
    ):
        mock_is_buildservice_worker.return_value = False
        mock_cmd_caps.return_value = True
        container = ContainerImageOCI('root_dir', 'oci-archive')
        assert container.oci_config == {
            'container_name': 'kiwi-container',
            'container_tag': 'latest',
            'history': {'created_by': 'KIWI {0}'.format(__version__)}
        }

    @patch('kiwi.container.oci.RuntimeConfig')
    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.defaults.Defaults.is_buildservice_worker')
    def test_init_in_buildservice(
        self, mock_buildservice, mock_cmd_caps, mock_RuntimeConfig
    ):
        mock_buildservice.return_value = True
        mock_cmd_caps.return_value = True

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            m_open.return_value.__iter__ = lambda _: \
                iter(['BUILD_DISTURL=obs://build.opensuse.org/some:project'])
            container = ContainerImageOCI(
                'root_dir', 'oci-archive'
            )

        m_open.assert_called_once_with('/.buildenv')
        assert container.oci_config['labels'] == {
            'org.openbuildservice.disturl':
            'obs://build.opensuse.org/some:project'
        }

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            m_open.return_value.__iter__ = lambda _: \
                iter(['BUILD_DISTURL=obs://build.opensuse.org/some:project'])
            container = ContainerImageOCI(
                'root_dir', 'oci-archive', {'labels': {'label': 'value'}}
            )

        m_open.assert_called_once_with('/.buildenv')
        assert container.oci_config['labels'] == {
            'label': 'value',
            'org.openbuildservice.disturl':
            'obs://build.opensuse.org/some:project'
        }

    @patch('kiwi.container.oci.RuntimeConfig')
    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.defaults.Defaults.is_buildservice_worker')
    def test_init_in_buildservice_without_disturl(
        self, mock_buildservice, mock_cmd_caps, mock_RuntimeConfig
    ):
        mock_buildservice.return_value = True
        mock_cmd_caps.return_value = True

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            m_open.return_value.__iter__ = lambda _: iter(['line content'])
            with self._caplog.at_level(logging.WARNING):
                container = ContainerImageOCI('root_dir', 'oci-archive')

        m_open.assert_called_once_with('/.buildenv')
        assert 'labels' not in container.oci_config

    @patch('kiwi.container.oci.OCI')
    @patch('kiwi.container.oci.Defaults.get_shared_cache_location')
    @patch('kiwi.container.oci.Compress')
    def test_create_oci_archive(self, mock_Compress, mock_cache, mock_OCI):
        compress = Mock()
        mock_Compress.return_value = compress
        mock_cache.return_value = 'var/cache/kiwi'
        mock_oci = Mock()
        mock_OCI.new.return_value.__enter__.return_value = mock_oci

        self.oci.archive_transport = 'oci-archive'
        self.oci.create('result.tar', '', True, True)

        mock_oci.init_container.assert_called_once_with()
        mock_oci.unpack.assert_called_once_with()
        mock_oci.sync_rootfs.assert_called_once_with(
            'root_dir', [
                'image', '.kconfig', 'run/*', 'tmp/*',
                '.buildenv', 'var/cache/kiwi', 'dev/*', 'sys/*', 'proc/*'
            ]
        )
        mock_oci.repack.assert_called_once_with(
            {
                'container_name': 'foo/bar',
                'additional_names': [':current', 'name:foobar', 'newname'],
                'container_tag': 'latest',
                'entry_subcommand': ['/bin/bash'],
                'history': {'created_by': 'KIWI {0}'.format(__version__)}
            }
        )
        mock_oci.set_config.assert_called_once_with(
            {
                'container_name': 'foo/bar',
                'additional_names': [':current', 'name:foobar', 'newname'],
                'container_tag': 'latest',
                'entry_subcommand': ['/bin/bash'],
                'history': {'created_by': 'KIWI {0}'.format(__version__)}
            }
        )
        mock_oci.post_process.assert_called_once_with()
        mock_oci.export_container_image.assert_called_once_with(
            'result.tar', 'oci-archive', 'foo/bar:latest', []
        )
        compress.xz.assert_called_once_with(
            self.runtime_config.get_xz_options.return_value
        )

    @patch('kiwi.container.oci.OCI')
    @patch('kiwi.container.oci.Defaults.get_shared_cache_location')
    def test_create_derived_docker_archive(
        self, mock_cache, mock_OCI
    ):
        mock_cache.return_value = 'var/cache/kiwi'
        mock_oci = Mock()
        mock_OCI.new.return_value.__enter__.return_value = mock_oci

        self.runtime_config.get_container_compression.return_value = 'xz'

        self.oci.create('result.tar', 'root_dir/image/image_file')

        mock_oci.import_container_image.assert_called_once_with(
            'oci-archive:root_dir/image/image_file:base_layer'
        )
        mock_oci.unpack.assert_called_once_with()
        mock_oci.sync_rootfs.assert_called_once_with(
            'root_dir', [
                'image', '.kconfig', 'run/*', 'tmp/*',
                '.buildenv', 'var/cache/kiwi', 'dev/*', 'sys/*', 'proc/*'
            ]
        )
        mock_oci.repack.assert_called_once_with({
            'container_name': 'foo/bar',
            'additional_names': [':current', 'name:foobar', 'newname'],
            'container_tag': 'latest',
            'history': {'created_by': 'KIWI {0}'.format(__version__)}
        })
        mock_oci.set_config.assert_called_once_with({
            'container_name': 'foo/bar',
            'additional_names': [':current', 'name:foobar', 'newname'],
            'container_tag': 'latest',
            'history': {'created_by': 'KIWI {0}'.format(__version__)}
        })
        mock_oci.post_process.assert_called_once_with()
        mock_oci.export_container_image.assert_called_once_with(
            'result.tar', 'docker-archive', 'foo/bar:latest',
            ['foo/bar:current', 'name:foobar', 'newname:latest']
        )
