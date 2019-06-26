from mock import patch

import mock

from .test_helper import patch_open

from kiwi.container.oci import ContainerImageOCI
from kiwi.version import __version__


class TestContainerImageOCI(object):
    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.container.oci.RuntimeConfig')
    def setup(self, mock_RuntimeConfig, mock_cmd_caps):
        mock_cmd_caps.return_value = True
        self.oci = ContainerImageOCI(
            'root_dir', 'docker-archive', {
                'container_name': 'foo/bar',
                'additional_tags': ['current', 'foobar']
            }
        )

    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    def test_init_custom_args(self, mock_cmd_caps):
        mock_cmd_caps.return_value = True
        custom_args = {
            'container_name': 'foo',
            'container_tag': '1.0',
            'additional_tags': ['current', 'foobar'],
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
    def test_init_without_custom_args(self, mock_cmd_caps):
        mock_cmd_caps.return_value = True
        container = ContainerImageOCI('root_dir', 'oci-archive')
        assert container.oci_config == {
            'container_name': 'kiwi-container',
            'container_tag': 'latest',
            'entry_subcommand': ['/bin/bash'],
            'history': {'created_by': 'KIWI {0}'.format(__version__)}
        }

    @patch('kiwi.container.oci.RuntimeConfig')
    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.defaults.Defaults.is_buildservice_worker')
    @patch_open
    def test_init_in_buildservice(
        self, mock_open, mock_buildservice, mock_cmd_caps, mock_RuntimeConfig
    ):
        mock_buildservice.return_value = True
        mock_cmd_caps.return_value = True
        handle = mock_open.return_value.__enter__.return_value
        handle.__iter__.return_value =\
            iter(['BUILD_DISTURL=obs://build.opensuse.org/some:project'])
        container = ContainerImageOCI('root_dir', 'oci-archive')
        mock_open.assert_called_once_with('/.buildenv')
        assert container.oci_config['labels'] == {
            'org.openbuildservice.disturl':
            'obs://build.opensuse.org/some:project'
        }

    @patch('kiwi.container.oci.RuntimeConfig')
    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.defaults.Defaults.is_buildservice_worker')
    @patch_open
    @patch('kiwi.logger.log.warning')
    def test_init_in_buildservice_without_disturl(
        self, mock_warn, mock_open, mock_buildservice,
        mock_cmd_caps, mock_RuntimeConfig
    ):
        mock_buildservice.return_value = True
        mock_cmd_caps.return_value = True
        handle = mock_open.return_value.__enter__.return_value
        handle.__iter__.return_value = iter(['line content'])
        container = ContainerImageOCI('root_dir', 'oci-archive')
        mock_open.assert_called_once_with('/.buildenv')
        assert 'labels' not in container.oci_config
        assert mock_warn.called

    @patch('kiwi.container.oci.OCI')
    @patch('kiwi.container.oci.Defaults.get_shared_cache_location')
    def test_create_oci_archive(self, mock_cache, mock_OCI):
        mock_cache.return_value = 'var/cache/kiwi'
        mock_oci = mock.Mock()
        mock_OCI.return_value = mock_oci

        self.oci.runtime_config.get_container_compression = mock.Mock(
            return_value=None
        )

        self.oci.archive_transport = 'oci-archive'
        self.oci.create('result.tar', None)

        mock_oci.init_container.assert_called_once_with()
        mock_oci.unpack.assert_called_once_with()
        mock_oci.sync_rootfs.assert_called_once_with(
            'root_dir', [
                'image', '.profile', '.kconfig', '.buildenv',
                'var/cache/kiwi', 'boot', 'dev', 'sys', 'proc'
            ]
        )
        mock_oci.repack.assert_called_once_with({
            'container_name': 'foo/bar',
            'additional_tags': ['current', 'foobar'],
            'container_tag': 'latest',
            'entry_subcommand': ['/bin/bash'],
            'history': {'created_by': 'KIWI {0}'.format(__version__)}
        })
        mock_oci.set_config.assert_called_once_with({
            'container_name': 'foo/bar',
            'additional_tags': ['current', 'foobar'],
            'container_tag': 'latest',
            'entry_subcommand': ['/bin/bash'],
            'history': {'created_by': 'KIWI {0}'.format(__version__)}
        })
        mock_oci.post_process.assert_called_once_with()
        mock_oci.export_container_image.assert_called_once_with(
            'result.tar', 'oci-archive', 'latest', []
        )

    @patch('kiwi.container.oci.Compress')
    @patch('kiwi.container.oci.OCI')
    @patch('kiwi.container.oci.Defaults.get_shared_cache_location')
    def test_create_derived_docker_archive(
        self, mock_cache, mock_OCI, mock_compress
    ):
        mock_cache.return_value = 'var/cache/kiwi'
        mock_oci = mock.Mock()
        mock_OCI.return_value = mock_oci

        self.oci.create('result.tar', 'root_dir/image/image_file')

        mock_oci.import_container_image.assert_called_once_with(
            'oci-archive:root_dir/image/image_file:base_layer'
        )
        mock_oci.unpack.assert_called_once_with()
        mock_oci.sync_rootfs.assert_called_once_with(
            'root_dir', [
                'image', '.profile', '.kconfig', '.buildenv',
                'var/cache/kiwi', 'boot', 'dev', 'sys', 'proc'
            ]
        )
        mock_oci.repack.assert_called_once_with({
            'container_name': 'foo/bar',
            'additional_tags': ['current', 'foobar'],
            'container_tag': 'latest',
            'entry_subcommand': ['/bin/bash'],
            'history': {'created_by': 'KIWI {0}'.format(__version__)}
        })
        mock_oci.set_config.assert_called_once_with({
            'container_name': 'foo/bar',
            'additional_tags': ['current', 'foobar'],
            'container_tag': 'latest',
            'entry_subcommand': ['/bin/bash'],
            'history': {'created_by': 'KIWI {0}'.format(__version__)}
        })
        mock_oci.post_process.assert_called_once_with()
        mock_oci.export_container_image.assert_called_once_with(
            'result.tar', 'docker-archive', 'foo/bar:latest',
            ['foo/bar:current', 'foo/bar:foobar']
        )

        mock_compress.assert_called_once_with('result.tar')
