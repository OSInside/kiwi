from unittest.mock import patch

from kiwi.container.setup.docker import ContainerSetupDocker


class TestContainerSetupDocker:
    @patch('os.path.exists')
    def test_init(self, mock_exists):
        mock_exists.return_value = True
        container = ContainerSetupDocker(
            'root_dir', {'container_name': 'system'}
        )
        assert container.custom_args['container_name'] == 'system'
