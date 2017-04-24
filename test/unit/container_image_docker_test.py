from mock import call
from mock import patch

from kiwi.container.docker import ContainerImageDocker


class TestContainerImageDocker(object):

    @patch('kiwi.container.docker.Compress')
    @patch('kiwi.container.oci.Command.run')
    def test_pack_image_to_file(self, mock_command, mock_compress):
        docker = ContainerImageDocker('root_dir', {'container_name': 'foo/bar'})
        docker.oci_dir = 'kiwi_oci_dir'
        docker.pack_image_to_file('result.tar.xz')

        assert mock_command.call_args_list == [
            call(['rm', '-r', '-f', 'result.tar']),
            call([
                'skopeo', 'copy', 'oci:kiwi_oci_dir/umoci_layout:latest',
                'docker-archive:result.tar:foo/bar:latest'
            ])
        ]
        mock_compress.assert_called_once_with('result.tar')
