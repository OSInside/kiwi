from mock import call
from mock import patch

import mock

from kiwi.container.oci import ContainerImageOCI


class TestContainerImageOCI(object):
    def setup(self):
        self.oci = ContainerImageOCI(
            'root_dir', {
                'container_name': 'foo/bar'
            }
        )

    def test_init_custom_args(self):
        custom_args = {
            'container_name': 'foo',
            'container_tag': '1.0',
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
            ],
            'xz_options': ['-a', '-b']
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
        assert container.xz_options == custom_args['xz_options']

    @patch('kiwi.container.oci.Path.wipe')
    def test_del(self, mock_wipe):
        self.oci.oci_dir = 'dir_a'
        self.oci.oci_root_dir = 'dir_b'
        self.oci.__del__()
        assert mock_wipe.call_args_list == [
            call('dir_a'), call('dir_b')
        ]

    @patch('kiwi.container.oci.datetime')
    @patch('kiwi.container.oci.ArchiveTar')
    @patch('kiwi.container.oci.Command.run')
    @patch('kiwi.container.oci.DataSync')
    @patch('kiwi.container.oci.mkdtemp')
    @patch('kiwi.container.oci.Defaults.get_shared_cache_location')
    def test_create(
        self, mock_cache, mock_mkdtemp,
        mock_sync, mock_command, mock_tar, mock_datetime
    ):
        strftime = mock.Mock()
        strftime.strftime = mock.Mock(return_value='current_date')
        mock_datetime.utcnow = mock.Mock(
            return_value=strftime
        )

        mock_cache.return_value = 'var/cache/kiwi'
        oci_root = mock.Mock()
        mock_sync.return_value = oci_root
        tmpdirs = ['kiwi_oci_root_dir', 'kiwi_oci_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp

        self.oci.create('result.tar.xz', None)

        assert mock_command.call_args_list == [
            call([
                'umoci', 'init', '--layout',
                'kiwi_oci_dir/umoci_layout'
            ]),
            call([
                'umoci', 'new', '--image',
                'kiwi_oci_dir/umoci_layout:latest'
            ]),
            call([
                'umoci', 'unpack', '--image',
                'kiwi_oci_dir/umoci_layout:latest', 'kiwi_oci_root_dir'
            ]),
            call([
                'umoci', 'repack', '--image',
                'kiwi_oci_dir/umoci_layout:latest', 'kiwi_oci_root_dir'
            ]),
            call([
                'umoci', 'config', '--config.cmd=/bin/bash', '--image',
                'kiwi_oci_dir/umoci_layout:latest', '--created', 'current_date'
            ]),
            call([
                'umoci', 'gc', '--layout', 'kiwi_oci_dir/umoci_layout'
            ])
        ]
        mock_sync.assert_called_once_with(
            'root_dir/', 'kiwi_oci_root_dir/rootfs'
        )
        oci_root.sync_data.assert_called_once_with(
            exclude=[
                'image', '.profile', '.kconfig', 'boot', 'dev', 'sys', 'proc',
                'var/cache/kiwi'
            ],
            options=['-a', '-H', '-X', '-A', '--delete']
        )

        mock_tar.called_once_with('result.tar.xz')

    @patch('kiwi.container.oci.datetime')
    @patch('kiwi.container.oci.ArchiveTar')
    @patch('kiwi.container.oci.Command.run')
    @patch('kiwi.container.oci.DataSync')
    @patch('kiwi.container.oci.mkdtemp')
    @patch('kiwi.container.oci.Path.create')
    @patch('kiwi.container.oci.Defaults.get_shared_cache_location')
    def test_create_derived(
        self, mock_cache, mock_create, mock_mkdtemp,
        mock_sync, mock_command, mock_tar, mock_datetime
    ):
        strftime = mock.Mock()
        strftime.strftime = mock.Mock(return_value='current_date')
        mock_datetime.utcnow = mock.Mock(
            return_value=strftime
        )

        mock_cache.return_value = 'var/cache/kiwi'
        oci_root = mock.Mock()
        mock_sync.return_value = oci_root
        tmpdirs = ['kiwi_oci_root_dir', 'kiwi_oci_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp

        self.oci.create('result.tar.xz', 'root_dir/image/image_file')

        mock_create.assert_called_once_with('kiwi_oci_dir/umoci_layout')

        assert mock_command.call_args_list == [
            call([
                'umoci', 'config', '--image',
                'kiwi_oci_dir/umoci_layout', '--tag', 'latest'
            ]),
            call([
                'umoci', 'unpack', '--image',
                'kiwi_oci_dir/umoci_layout:latest', 'kiwi_oci_root_dir'
            ]),
            call([
                'umoci', 'repack', '--image',
                'kiwi_oci_dir/umoci_layout:latest', 'kiwi_oci_root_dir'
            ]),
            call([
                'umoci', 'config', '--config.cmd=/bin/bash', '--image',
                'kiwi_oci_dir/umoci_layout:latest', '--created', 'current_date'
            ]),
            call([
                'umoci', 'gc', '--layout', 'kiwi_oci_dir/umoci_layout'
            ])
        ]
        mock_sync.assert_called_once_with(
            'root_dir/', 'kiwi_oci_root_dir/rootfs'
        )
        oci_root.sync_data.assert_called_once_with(
            exclude=[
                'image', '.profile', '.kconfig', 'boot', 'dev', 'sys', 'proc',
                'var/cache/kiwi'
            ],
            options=['-a', '-H', '-X', '-A', '--delete']
        )
        mock_tar.call_args_list == [
            call('root_dir/image/image_file'), call('result.tar.xz')
        ]
