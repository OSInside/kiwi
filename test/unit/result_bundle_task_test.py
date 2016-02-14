import sys
import mock
from nose.tools import *
from mock import patch
from mock import call
import kiwi

import nose_helper
from kiwi.exceptions import *
from kiwi.result_bundle_task import ResultBundleTask


class TestResultBundleTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], 'result', 'bundle', '--target-dir', 'target_dir',
            '--bundle-dir', 'bundle_dir', '--id', 'Build_42'
        ]
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        self.file_mock.read.return_value = 'data'

        self.result = mock.Mock()
        self.result.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        kiwi.result_bundle_task.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = ResultBundleTask()

    def __init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['bundle'] = False
        self.task.command_args['--target-dir'] = 'target_dir'
        self.task.command_args['--bundle-dir'] = 'bundle_dir'
        self.task.command_args['--id'] = 'Build_42'

    @raises(KiwiBundleError)
    def test_process_invalid_bundle_directory(self):
        self.__init_command_args()
        self.task.command_args['--bundle-dir'] = \
            self.task.command_args['--target-dir']
        self.task.command_args['bundle'] = True
        self.task.process()

    @raises(KiwiRequestedTypeError)
    @patch('kiwi.result_bundle_task.Result.load')
    def test_process_invalid_type_for_bundle(self, mock_load):
        self.result.xml_state.get_build_type_name = mock.Mock(
            return_value='foo'
        )
        mock_load.return_value = self.result
        self.__init_command_args()
        self.task.command_args['bundle'] = True
        self.task.process()

    @patch('kiwi.result_bundle_task.Result.load')
    @patch('kiwi.result_bundle_task.Command.run')
    @patch('kiwi.result_bundle_task.Path.create')
    @patch('kiwi.result_bundle_task.Compress')
    @patch('kiwi.result_bundle_task.hashlib.sha256')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    def test_process_result_bundle_container(
        self, mock_open, mock_exists, mock_sha256, mock_compress,
        mock_path, mock_command, mock_load
    ):
        compress = mock.Mock()
        sha256 = mock.Mock()
        mock_sha256.return_value = sha256
        mock_compress.return_value = compress
        mock_exists.return_value = False
        mock_open.return_value = self.context_manager_mock
        self.result.xml_state.get_build_type_name = mock.Mock(
            return_value='docker'
        )
        self.result.get_results = mock.Mock(
            return_value={'container': 'some-container-1.2.3'}
        )
        mock_load.return_value = self.result
        self.__init_command_args()
        self.task.command_args['bundle'] = True
        self.task.process()

        mock_load.assert_called_once_with('target_dir/kiwi.result')
        mock_path.assert_called_once_with('bundle_dir')
        mock_command.assert_called_once_with(
            [
                'cp', '-l', 'some-container-1.2.3',
                'bundle_dir/some-container-1.2.3-Build_42'
            ]
        )
        mock_compress.assert_called_once_with(
            'bundle_dir/some-container-1.2.3-Build_42'
        )
        compress.xz.assert_called_once_with()
        mock_sha256.assert_called_once_with('data')
        sha256.hexdigest.assert_called_once_with()

    @patch('kiwi.result_bundle_task.Result.load')
    @patch('kiwi.result_bundle_task.Command.run')
    @patch('kiwi.result_bundle_task.Path.create')
    @patch('kiwi.result_bundle_task.Compress')
    @patch('kiwi.result_bundle_task.hashlib.sha256')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    def test_process_result_bundle_filesystem_image(
        self, mock_open, mock_exists, mock_sha256, mock_compress,
        mock_path, mock_command, mock_load
    ):
        sha256 = mock.Mock()
        mock_sha256.return_value = sha256
        mock_open.return_value = self.context_manager_mock
        self.result.xml_state.get_build_type_name = mock.Mock(
            return_value='ext4'
        )
        self.result.get_results = mock.Mock(
            return_value={'filesystem_image': 'some-fs-1.2.3'}
        )
        mock_load.return_value = self.result
        self.__init_command_args()
        self.task.command_args['bundle'] = True
        self.task.process()

        mock_command.assert_called_once_with(
            [
                'cp', '-l', 'some-fs-1.2.3',
                'bundle_dir/some-fs-1.2.3-Build_42'
            ]
        )
        mock_compress.assert_called_once_with(
            'bundle_dir/some-fs-1.2.3-Build_42'
        )
        sha256.hexdigest.assert_called_once_with()

    @patch('kiwi.result_bundle_task.Result.load')
    @patch('kiwi.result_bundle_task.Command.run')
    @patch('kiwi.result_bundle_task.Path.create')
    @patch('kiwi.result_bundle_task.Compress')
    @patch('kiwi.result_bundle_task.hashlib.sha256')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    def test_process_result_bundle_disk_image(
        self, mock_open, mock_exists, mock_sha256, mock_compress,
        mock_path, mock_command, mock_load
    ):
        sha256 = mock.Mock()
        mock_sha256.return_value = sha256
        mock_open.return_value = self.context_manager_mock
        self.result.xml_state.get_build_type_name = mock.Mock(
            return_value='oem'
        )
        self.result.get_results = mock.Mock(
            return_value={
                'disk_image': 'some-disk-1.2.3',
                'installation_image': 'some-install-1.2.3.iso',
                'installation_pxe_archive': 'some-install-archive-1.2.3.tbz',
                'disk_format_image': 'some-format-1.2.3.qcow2'
            }
        )
        mock_load.return_value = self.result
        self.__init_command_args()
        self.task.command_args['bundle'] = True
        self.task.process()

        assert mock_command.call_args_list == [
            call([
                'cp', '-l', 'some-disk-1.2.3',
                'bundle_dir/some-disk-1.2.3-Build_42'
            ]),
            call([
                'cp', '-l', 'some-install-1.2.3.iso',
                'bundle_dir/some-install-1.2.3-Build_42.iso'
            ]),
            call([
                'cp', '-l', 'some-install-archive-1.2.3.tbz',
                'bundle_dir/some-install-archive-1.2.3-Build_42.tbz'
            ]),
            call([
                'cp', '-l', 'some-format-1.2.3.qcow2',
                'bundle_dir/some-format-1.2.3-Build_42.qcow2'
            ])
        ]
        assert mock_compress.call_args_list == [
            call('bundle_dir/some-disk-1.2.3-Build_42'),
            call('bundle_dir/some-format-1.2.3-Build_42.qcow2')
        ]
        assert len(sha256.hexdigest.call_args_list) == 4

    @patch('kiwi.result_bundle_task.Result.load')
    @patch('kiwi.result_bundle_task.Command.run')
    @patch('kiwi.result_bundle_task.Path.create')
    @patch('kiwi.result_bundle_task.Compress')
    @patch('kiwi.result_bundle_task.hashlib.sha256')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    def test_process_result_bundle_live_image(
        self, mock_open, mock_exists, mock_sha256, mock_compress,
        mock_path, mock_command, mock_load
    ):
        sha256 = mock.Mock()
        mock_sha256.return_value = sha256
        mock_open.return_value = self.context_manager_mock
        self.result.xml_state.get_build_type_name = mock.Mock(
            return_value='iso'
        )
        self.result.get_results = mock.Mock(
            return_value={'live_image': 'some-live-1.2.3'}
        )
        mock_load.return_value = self.result
        self.__init_command_args()
        self.task.command_args['bundle'] = True
        self.task.process()

        mock_command.assert_called_once_with(
            [
                'cp', '-l', 'some-live-1.2.3',
                'bundle_dir/some-live-1.2.3-Build_42'
            ]
        )
        assert mock_compress.call_args_list == []
        sha256.hexdigest.assert_called_once_with()

    @patch('kiwi.result_bundle_task.Result.load')
    @patch('kiwi.result_bundle_task.Command.run')
    @patch('kiwi.result_bundle_task.Path.create')
    @patch('kiwi.result_bundle_task.Compress')
    @patch('kiwi.result_bundle_task.hashlib.sha256')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    def test_process_result_bundle_archive_image(
        self, mock_open, mock_exists, mock_sha256, mock_compress,
        mock_path, mock_command, mock_load
    ):
        sha256 = mock.Mock()
        mock_sha256.return_value = sha256
        mock_open.return_value = self.context_manager_mock
        self.result.xml_state.get_build_type_name = mock.Mock(
            return_value='tbz'
        )
        self.result.get_results = mock.Mock(
            return_value={'root_archive': 'some-tar-1.2.3'}
        )
        mock_load.return_value = self.result
        self.__init_command_args()
        self.task.command_args['bundle'] = True
        self.task.process()

        mock_command.assert_called_once_with(
            [
                'cp', '-l', 'some-tar-1.2.3',
                'bundle_dir/some-tar-1.2.3-Build_42'
            ]
        )
        assert mock_compress.call_args_list == []
        sha256.hexdigest.assert_called_once_with()

    @patch('kiwi.result_bundle_task.Result.load')
    @patch('kiwi.result_bundle_task.Command.run')
    @patch('kiwi.result_bundle_task.Path.create')
    @patch('kiwi.result_bundle_task.Compress')
    @patch('kiwi.result_bundle_task.hashlib.sha256')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    def test_process_result_bundle_pxe_image(
        self, mock_open, mock_exists, mock_sha256, mock_compress,
        mock_path, mock_command, mock_load
    ):
        sha256 = mock.Mock()
        mock_sha256.return_value = sha256
        mock_open.return_value = self.context_manager_mock
        self.result.xml_state.get_build_type_name = mock.Mock(
            return_value='pxe'
        )
        self.result.get_results = mock.Mock(
            return_value={
                'filesystem_image': 'some-fs-1.2.3.ext3',
                'filesystem_md5': 'some-fs-1.2.3.md5',
                'kernel': 'some.kernel',
                'initrd': 'some.initrd',
                'xen_hypervisor': 'xen.gz'
            }
        )
        mock_load.return_value = self.result
        self.__init_command_args()
        self.task.command_args['bundle'] = True
        self.task.process()

        assert mock_command.call_args_list == [
            call([
                'cp', '-l', 'some-fs-1.2.3.ext3',
                'bundle_dir/some-fs-1.2.3-Build_42.ext3'
            ]),
            call([
                'cp', '-l', 'some-fs-1.2.3.md5',
                'bundle_dir/some-fs-1.2.3-Build_42.md5'
            ]),
            call([
                'cp', '-l', 'some.kernel', 'bundle_dir/some.kernel'
            ]),
            call([
                'cp', '-l', 'some.initrd', 'bundle_dir/some.initrd'
            ]),
            call([
                'cp', '-l', 'xen.gz', 'bundle_dir/xen.gz'
            ])
        ]
        assert mock_compress.call_args_list == []
        assert len(sha256.hexdigest.call_args_list) == 5

    def test_process_result_bundle_help(self):
        self.__init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['bundle'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::result::bundle'
        )
