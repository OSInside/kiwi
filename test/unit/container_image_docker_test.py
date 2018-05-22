from mock import (
    call, patch, Mock
)

from kiwi.container.docker import ContainerImageDocker


class TestContainerImageDocker(object):
    @patch('kiwi.container.docker.Compress')
    @patch('kiwi.container.oci.Command.run')
    @patch('kiwi.container.oci.RuntimeConfig')
    def test_pack_image_to_file(
        self, mock_RuntimeConfig, mock_command, mock_compress
    ):
        compressor = Mock()
        compressor.xz = Mock(
            return_value='result.tar.xz'
        )
        mock_compress.return_value = compressor
        docker = ContainerImageDocker(
            'root_dir', {
                'container_name': 'foo/bar',
                'additional_tags': ['current', 'foobar']
            }
        )
        docker.oci_dir = 'kiwi_oci_dir'
        docker.runtime_config.get_container_compression = Mock(
            return_value='xz'
        )

        assert docker.pack_image_to_file('result.tar') == 'result.tar.xz'

        assert mock_command.call_args_list == [
            call(['rm', '-r', '-f', 'result.tar']),
            call([
                'skopeo', 'copy', 'oci:kiwi_oci_dir/umoci_layout:latest',
                'docker-archive:result.tar:foo/bar:latest',
                '--additional-tag', 'foo/bar:current',
                '--additional-tag', 'foo/bar:foobar'
            ])
        ]
        mock_compress.assert_called_once_with('result.tar')
        compressor.xz.assert_called_once_with(
            docker.runtime_config.get_xz_options.return_value
        )

        docker.runtime_config.get_container_compression = Mock(
            return_value=None
        )

        assert docker.pack_image_to_file('result.tar') == 'result.tar'
