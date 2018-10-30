from mock import call
from mock import patch

import mock

from .test_helper import patch_open

from kiwi.container.oci import ContainerImageOCI


class TestContainerImageOCI(object):
    @patch('kiwi.container.oci.RuntimeConfig')
    @patch('kiwi.container.oci.OCI')
    def setup(self, mock_OCI, mock_RuntimeConfig):
        oci = mock.Mock()
        oci.container_dir = 'kiwi_oci_dir.XXXX/oci_layout'
        mock_OCI.return_value = oci
        self.oci = ContainerImageOCI(
            'root_dir', {
                'container_name': 'foo/bar',
                'additional_tags': ['current', 'foobar']
            }
        )

    def test_init_custom_args(self):
        custom_args = {
            'container_name': 'foo',
            'container_tag': '1.0',
            'additional_tags': ['current', 'foobar'],
            'entry_command': [
                '--config.entrypoint=/bin/bash',
                '--config.entrypoint=-x'
            ],
            'entry_subcommand': [
                '--config.cmd=ls',
                '--config.cmd=-l'
            ],
            'maintainer': ['--author=tux'],
            'user': ['--config.user=root'],
            'workingdir': ['--config.workingdir=/root'],
            'expose_ports': [
                '--config.exposedports=80',
                '--config.exposedports=42'
            ],
            'volumes': [
                '--config.volume=/var/log',
                '--config.volume=/tmp'
            ],
            'environment': [
                '--config.env=PATH=/bin',
                '--config.env=FOO=bar'
            ],
            'labels': [
                '--config.label=a=value',
                '--config.label=b=value'
            ]
        }
        container = ContainerImageOCI(
            'root_dir', custom_args
        )
        assert container.container_name == custom_args['container_name']
        assert container.container_tag == custom_args['container_tag']
        assert container.entry_command == custom_args['entry_command']
        assert container.entry_subcommand == custom_args['entry_subcommand']
        assert container.maintainer == custom_args['maintainer']
        assert container.user == custom_args['user']
        assert container.workingdir == custom_args['workingdir']
        assert container.expose_ports == custom_args['expose_ports']
        assert container.volumes == custom_args['volumes']
        assert container.environment == custom_args['environment']
        assert container.labels == custom_args['labels']
        assert container.additional_tags == custom_args['additional_tags']

    def test_init_without_custom_args(self):
        container = ContainerImageOCI('root_dir')
        assert container.container_name == 'kiwi-container'
        assert container.container_tag == 'latest'
        assert container.additional_tags == []

    @patch('kiwi.defaults.Defaults.is_buildservice_worker')
    @patch_open
    def test_init_in_buildservice(self, mock_open, mock_buildservice):
        mock_buildservice.return_value = True
        handle = mock_open.return_value.__enter__.return_value
        handle.__iter__.return_value =\
            iter(['BUILD_DISTURL=obs://build.opensuse.org/some:project'])
        container = ContainerImageOCI('root_dir')
        mock_open.assert_called_once_with('/.buildenv')
        assert container.labels == [
            '--config.label=org.openbuildservice.disturl='
            'obs://build.opensuse.org/some:project'
        ]

    @patch('kiwi.defaults.Defaults.is_buildservice_worker')
    @patch_open
    @patch('kiwi.logger.log.warning')
    def test_init_in_buildservice_without_disturl(
        self, mock_warn, mock_open, mock_buildservice
    ):
        mock_buildservice.return_value = True
        handle = mock_open.return_value.__enter__.return_value
        handle.__iter__.return_value = iter(['line content'])
        container = ContainerImageOCI('root_dir')
        mock_open.assert_called_once_with('/.buildenv')
        assert container.labels == []
        assert mock_warn.called

    @patch('kiwi.container.oci.Path.wipe')
    def test_del(self, mock_wipe):
        self.oci.oci_root_dir = 'kiwi_oci_root_dir'
        self.oci.__del__()
        mock_wipe.assert_called_once_with('kiwi_oci_root_dir')

    @patch('kiwi.container.oci.ArchiveTar')
    @patch('kiwi.container.oci.DataSync')
    @patch('kiwi.container.oci.mkdtemp')
    @patch('kiwi.container.oci.Defaults.get_shared_cache_location')
    def test_create(
        self, mock_cache, mock_mkdtemp, mock_sync, mock_tar
    ):
        oci_tarfile = mock.Mock()
        mock_tar.return_value = oci_tarfile

        mock_cache.return_value = 'var/cache/kiwi'
        oci_root = mock.Mock()
        mock_sync.return_value = oci_root

        mock_mkdtemp.return_value = 'kiwi_oci_root_dir'

        self.oci.runtime_config.get_container_compression = mock.Mock(
            return_value='xz'
        )

        self.oci.create('result.tar', None)

        self.oci.oci.init_layout.assert_called_once_with(None)
        self.oci.oci.unpack.assert_called_once_with('kiwi_oci_root_dir')
        self.oci.oci.repack.assert_called_once_with('kiwi_oci_root_dir')
        self.oci.oci.set_config.assert_called_once_with(
            ['--config.cmd=/bin/bash']
        )
        assert self.oci.oci.add_tag.call_args_list == [
            call('current'), call('foobar')
        ]
        self.oci.oci.garbage_collect.assert_called_once_with()

        mock_sync.assert_called_once_with(
            'root_dir/', 'kiwi_oci_root_dir/rootfs'
        )
        oci_root.sync_data.assert_called_once_with(
            exclude=[
                'image', '.profile', '.kconfig', '.buildenv',
                'var/cache/kiwi', 'boot', 'dev', 'sys', 'proc',
            ],
            options=['-a', '-H', '-X', '-A', '--delete']
        )
        mock_tar.assert_called_once_with('result.tar')
        oci_tarfile.create_xz_compressed.assert_called_once_with(
            'kiwi_oci_dir.XXXX/oci_layout',
            xz_options=self.oci.runtime_config.get_xz_options.return_value
        )

        self.oci.runtime_config.get_container_compression = mock.Mock(
            return_value=None
        )

        self.oci.create('result.tar', None)

        oci_tarfile.create.assert_called_once_with(
            'kiwi_oci_dir.XXXX/oci_layout'
        )

    @patch('kiwi.container.oci.ArchiveTar')
    @patch('kiwi.container.oci.DataSync')
    @patch('kiwi.container.oci.mkdtemp')
    @patch('kiwi.container.oci.Path.create')
    @patch('kiwi.container.oci.Defaults.get_shared_cache_location')
    def test_create_derived(
        self, mock_cache, mock_create, mock_mkdtemp, mock_sync, mock_tar
    ):
        mock_cache.return_value = 'var/cache/kiwi'
        oci_root = mock.Mock()
        mock_sync.return_value = oci_root

        mock_mkdtemp.return_value = 'kiwi_oci_root_dir'

        self.oci.create('result.tar', 'root_dir/image/image_file')

        mock_create.assert_called_once_with('kiwi_oci_dir.XXXX/oci_layout')

        self.oci.oci.init_layout.assert_called_once_with(
            'root_dir/image/image_file'
        )
        self.oci.oci.unpack.assert_called_once_with('kiwi_oci_root_dir')
        self.oci.oci.repack.assert_called_once_with('kiwi_oci_root_dir')
        self.oci.oci.set_config.assert_called_once_with(
            ['--config.cmd=/bin/bash']
        )
        assert self.oci.oci.add_tag.call_args_list == [
            call('current'), call('foobar')
        ]
        self.oci.oci.garbage_collect.assert_called_once_with()

        mock_sync.assert_called_once_with(
            'root_dir/', 'kiwi_oci_root_dir/rootfs'
        )
        oci_root.sync_data.assert_called_once_with(
            exclude=[
                'image', '.profile', '.kconfig', '.buildenv',
                'var/cache/kiwi', 'boot', 'dev', 'sys', 'proc'
            ],
            options=['-a', '-H', '-X', '-A', '--delete']
        )
        assert mock_tar.call_args_list == [
            call('root_dir/image/image_file'), call('result.tar')
        ]
