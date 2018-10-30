from mock import (
    call, patch, Mock
)

from kiwi.container.docker import ContainerImageDocker


class TestContainerImageDocker(object):
    @patch('kiwi.container.docker.Compress')
    @patch('kiwi.container.docker.Command.run')
    @patch('kiwi.container.oci.RuntimeConfig')
    @patch('kiwi.container.oci.OCI')
    def test_pack_image_to_file(
        self, mock_OCI, mock_RuntimeConfig, mock_command, mock_compress
    ):
        oci = Mock()
        oci.container_name = 'kiwi_oci_dir.XXXX/oci_layout:latest'
        mock_OCI.return_value = oci
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
        docker.runtime_config.get_container_compression = Mock(
            return_value='xz'
        )

        assert docker.pack_image_to_file('result.tar') == 'result.tar.xz'

        assert mock_command.call_args_list == [
            call(['rm', '-r', '-f', 'result.tar']),
            call([
                'skopeo', 'copy', 'oci:kiwi_oci_dir.XXXX/oci_layout:latest',
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
