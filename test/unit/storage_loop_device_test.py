from mock import patch

from .test_helper import raises

from kiwi.exceptions import KiwiLoopSetupError

from kiwi.storage.loop_device import LoopDevice


class TestLoopDevice(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = False
        self.loop = LoopDevice('loop-file', 20, 4096)

    @raises(KiwiLoopSetupError)
    def test_loop_setup_invalid(self):
        LoopDevice('loop-file-does-not-exist-and-no-size-given')

    def test_get_device(self):
        assert self.loop.get_device() is None

    def test_is_loop(self):
        assert self.loop.is_loop() is True

    @patch('os.path.exists')
    @patch('kiwi.storage.loop_device.Command.run')
    def test_create(self, mock_command, mock_exists):
        mock_exists.return_value = False
        self.loop.create()
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'qemu-img', 'create', 'loop-file', '20M'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call([
                'losetup', '--logical-blocksize', '4096',
                '-f', '--show', 'loop-file'
            ])
        self.loop.node_name = None

    @patch('kiwi.storage.loop_device.Command.run')
    @patch('kiwi.logger.log.warning')
    def test_destructor(self, mock_log_warn, mock_command):
        self.loop.node_name = '/dev/loop0'
        mock_command.side_effect = Exception
        self.loop.__del__()
        mock_command.assert_called_once_with(
            ['losetup', '-d', '/dev/loop0']
        )
        assert mock_log_warn.called
        self.loop.node_name = None
