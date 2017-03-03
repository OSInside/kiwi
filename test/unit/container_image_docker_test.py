from mock import call
from mock import patch

import mock

from .test_helper import *

from kiwi.exceptions import *
from kiwi.container.docker import ContainerImageDocker


class TestContainerImageDocker(object):

    @patch('kiwi.container.docker.mkdtemp') 
    def setup(self, mock_mkdtemp):
        tmpdirs = ['kiwi_docker_root_dir', 'kiwi_docker_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp
        self.docker = ContainerImageDocker(
            'root_dir', {
                'container_name': 'foo/bar'
            }
        )

    def test_init_custom_args(self):
        docker = ContainerImageDocker(
            'root_dir', {
                'container_name': 'foo',
                'container_tag': '1.0',
                'entry_command': [
                    "--config.entrypoint=/bin/bash",
                    "--config.entrypoint=-x"
                 ],
                'entry_subcommand': [
                    "--config.cmd=ls",
                    "--config.cmd=-l"
                 ],
                 'maintainer': ['--author=tux'],
                 'user': ['--config.user=root'],
                 'workingdir': ['--config.workingdir=/root'],
                 'expose_ports': [
                     "--config.exposedports=80",
                     "--config.exposedports=42"
                 ],
                 'volumes': [
                     "--config.volume=/var/log",
                     "--config.volume=/tmp"
                 ],
                 'environment': [
                     "--config.env=PATH=/bin'",
                     "--config.env=FOO=bar"
                 ],
                 'labels': [
                     "--config.label=a=value",
                     "--config.label=b=value"
                 ]
            }
        )

    @patch('kiwi.container.docker.Path.wipe')
    def test_del(self, mock_wipe):
        self.docker.__del__()
        assert mock_wipe.call_args_list == [
            call('kiwi_docker_dir'), call('kiwi_docker_root_dir')
        ]

    @patch('kiwi.container.docker.Compress')
    @patch('kiwi.container.docker.Command.run')
    @patch('kiwi.container.docker.DataSync')
    @patch('kiwi.container.docker.Path.wipe')
    def test_create_base_image(
        self, mock_wipe, mock_sync, mock_command, mock_compress
    ):
        compressor = mock.Mock()
        mock_compress.return_value = compressor
        docker_root = mock.Mock()
        mock_sync.return_value = docker_root

        self.docker.create('result.tar.xz', None)

        mock_wipe.assert_called_once_with('result.tar')

        assert mock_command.call_args_list == [
            call([
                'umoci', 'init', '--layout',
                'kiwi_docker_dir/umoci_layout'
            ]),
            call([
                'umoci', 'new', '--image',
                'kiwi_docker_dir/umoci_layout:latest'
            ]),
            call([
                'umoci', 'unpack', '--image',
                'kiwi_docker_dir/umoci_layout:latest', 'kiwi_docker_root_dir'
            ]),
            call([
                'umoci', 'repack', '--image',
                'kiwi_docker_dir/umoci_layout:latest', 'kiwi_docker_root_dir'
            ]),
            call([
                'umoci', 'config', '--config.cmd=/bin/bash', '--image',
                'kiwi_docker_dir/umoci_layout:latest', '--tag', 'latest'
            ]),
            call([
                'umoci', 'gc', '--layout', 'kiwi_docker_dir/umoci_layout'
            ]),
            call([
                 'skopeo', 'copy', 'oci:kiwi_docker_dir/umoci_layout:latest',
                 'docker-archive:result.tar:foo/bar:latest'
            ])
        ]
        mock_sync.assert_called_once_with(
            'root_dir/', 'kiwi_docker_root_dir/rootfs'
        )
        docker_root.sync_data.assert_called_once_with(
            exclude=[
                'image', '.profile', '.kconfig', 'boot', 'dev', 'sys', 'proc',
                'var/cache/kiwi'
            ],
            options=['-a', '-H', '-X', '-A']
        )
        mock_compress.assert_called_once_with('result.tar')
        compressor.xz.assert_called_once_with()

    @patch('kiwi.container.docker.mkdtemp')
    @patch('kiwi.container.docker.Compress')
    @patch('kiwi.container.docker.Command.run')
    @patch('kiwi.container.docker.DataSync')
    @patch('kiwi.container.docker.Path.wipe')
    def test_create_derived_image(
        self, mock_wipe, mock_sync, mock_command, mock_compress, mock_mkdtemp
    ):
        tmpdirs = ['kiwi_docker_root_dir', 'kiwi_docker_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp
        docker = ContainerImageDocker(
            'root_dir', {
                'container_name': 'foo/bar',
                'container_tag': '1.0'
            }
        )
        compressor = mock.Mock()
        compressor.uncompressed_filename = 'base_image.tar'
        mock_compress.return_value = compressor

        docker_root = mock.Mock()
        mock_sync.return_value = docker_root

        docker.create('result.tar.xz', 'base_image.tar.xz')

        compressor.uncompress.assert_called_once_with(True)
        mock_wipe.assert_called_once_with('result.tar')

        assert mock_command.call_args_list == [
            call([
                'skopeo', 'copy', 'docker-archive:base_image.tar',
                'oci:kiwi_docker_dir/umoci_layout:1.0'
            ]),
            call([
                'umoci', 'unpack', '--image',
                'kiwi_docker_dir/umoci_layout:1.0', 'kiwi_docker_root_dir'
            ]),
            call([
                'umoci', 'repack', '--image',
                'kiwi_docker_dir/umoci_layout:1.0', 'kiwi_docker_root_dir'
            ]),
            call([
                'umoci', 'config', '--config.cmd=/bin/bash', '--image',
                'kiwi_docker_dir/umoci_layout:1.0', '--tag', '1.0'
            ]),
            call([
                'umoci', 'gc', '--layout', 'kiwi_docker_dir/umoci_layout'
            ]),
            call([
                 'skopeo', 'copy', 'oci:kiwi_docker_dir/umoci_layout:1.0',
                 'docker-archive:result.tar:foo/bar:1.0'
            ])
        ]
        mock_sync.assert_called_once_with(
            'root_dir/', 'kiwi_docker_root_dir/rootfs'
        )
        docker_root.sync_data.assert_called_once_with(
            exclude=[
                'image', '.profile', '.kconfig', 'boot', 'dev', 'sys', 'proc',
                'var/cache/kiwi'
            ],
            options=['-a', '-H', '-X', '-A']
        )
        assert mock_compress.call_args_list == [
            call('base_image.tar.xz'), call('result.tar')
        ]
        compressor.xz.assert_called_once_with()

    @patch('kiwi.container.docker.mkdtemp')
    @patch('kiwi.container.docker.Compress')
    @patch('kiwi.container.docker.Command.run')
    @patch('kiwi.container.docker.DataSync')
    def test_unpack_to_root_dir(
        self, mock_sync, mock_command, mock_compress, mock_mkdtemp
    ):
        tmpdirs = ['kiwi_docker_root_dir', 'kiwi_docker_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp
        docker = ContainerImageDocker(
            'root_dir', {
                'container_name': 'foo/bar',
                'container_tag': '1.0'
            }
        )
        compressor = mock.Mock()
        compressor.uncompressed_filename = 'base_image.tar'
        mock_compress.return_value = compressor

        docker_root = mock.Mock()
        mock_sync.return_value = docker_root

        docker.unpack_to_root_dir('base_image.tar.xz')

        mock_compress.assert_called_once_with('base_image.tar.xz')
        compressor.uncompress.assert_called_once_with(True)

        assert mock_command.call_args_list == [
            call([
                'skopeo', 'copy', 'docker-archive:base_image.tar',
                'oci:kiwi_docker_dir/umoci_layout:1.0'
            ]),
            call([
                'umoci', 'unpack', '--image',
                'kiwi_docker_dir/umoci_layout:1.0', 'kiwi_docker_root_dir'
            ]),
        ]
        mock_sync.assert_called_once_with(
            'kiwi_docker_root_dir/rootfs/', 'root_dir/'
        )
        docker_root.sync_data.assert_called_once_with(
            options=['-a', '-H', '-X', '-A']
        )
