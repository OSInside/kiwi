import os
import sys
import logging
from mock import (
    patch, call, Mock, mock_open
)
from pytest import (
    raises, fixture
)

from ..test_helper import argv_kiwi_tests

import kiwi
from kiwi.tasks.result_bundle import ResultBundleTask
from kiwi.system.result import Result

from kiwi.exceptions import KiwiBundleError


class TestResultBundleTask:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        sys.argv = [
            sys.argv[0], 'result', 'bundle', '--target-dir', 'target_dir',
            '--bundle-dir', 'bundle_dir', '--id', 'Build_42'
        ]
        self.abs_target_dir = os.path.abspath('target_dir')
        self.abs_bundle_dir = os.path.abspath('bundle_dir')

        self.xml_state = Mock()
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        self.xml_state.xml_data.get_name = Mock(
            return_value='test-image'
        )

        self.result = Result(self.xml_state)
        self.result.add(
            key='keyname', filename='test-image-1.2.3',
            use_for_bundle=True, compress=True, shasum=True
        )

        kiwi.tasks.result_bundle.Help = Mock(
            return_value=Mock()
        )
        self.task = ResultBundleTask()

        runtime_config = Mock()
        runtime_config.is_bundle_compression_requested = Mock(
            return_value=True
        )
        self.task.runtime_config = runtime_config

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['bundle'] = False
        self.task.command_args['--target-dir'] = 'target_dir'
        self.task.command_args['--bundle-dir'] = 'bundle_dir'
        self.task.command_args['--id'] = 'Build_42'
        self.task.command_args['--zsync-source'] = None
        self.task.command_args['--package-as-rpm'] = None

    def test_process_invalid_bundle_directory(self):
        self._init_command_args()
        self.task.command_args['--bundle-dir'] = \
            self.task.command_args['--target-dir']
        self.task.command_args['bundle'] = True
        with raises(KiwiBundleError):
            self.task.process()

    @patch('kiwi.tasks.result_bundle.Result.load')
    @patch('kiwi.tasks.result_bundle.Command.run')
    @patch('kiwi.tasks.result_bundle.Path.create')
    @patch('kiwi.tasks.result_bundle.Path.which')
    @patch('kiwi.tasks.result_bundle.Compress')
    @patch('kiwi.tasks.result_bundle.Checksum')
    @patch('os.path.exists')
    def test_process_result_bundle(
        self, mock_exists, mock_checksum, mock_compress,
        mock_path_which, mock_path_create, mock_command, mock_load
    ):
        # This file won't be copied with build id
        self.result.add(
            key='noversion', filename='test-image-noversion',
            use_for_bundle=True, compress=False, shasum=False
        )

        checksum = Mock()
        compress = Mock()
        mock_path_which.return_value = 'zsyncmake'
        compress.compressed_filename = 'compressed_filename'
        mock_compress.return_value = compress
        mock_checksum.return_value = checksum
        mock_exists.return_value = False
        mock_load.return_value = self.result
        self._init_command_args()
        self.task.command_args['bundle'] = True
        self.task.command_args['--zsync-source'] = 'http://example.com/zsync'

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.task.process()

        mock_load.assert_called_once_with(
            os.sep.join([self.abs_target_dir, 'kiwi.result'])
        )
        mock_path_create.assert_called_once_with(self.abs_bundle_dir)
        assert mock_command.call_args_list == [
            call([
                'cp', 'test-image-1.2.3',
                os.sep.join([self.abs_bundle_dir, 'test-image-1.2.3-Build_42'])
            ]),
            call([
                'zsyncmake', '-e',
                '-u', 'http://example.com/zsync/compressed_filename',
                '-o', 'compressed_filename.zsync',
                'compressed_filename'
            ]),
            call([
                'cp', 'test-image-noversion',
                os.sep.join([self.abs_bundle_dir, 'test-image-noversion'])
            ])
        ]
        mock_compress.assert_called_once_with(
            os.sep.join([self.abs_bundle_dir, 'test-image-1.2.3-Build_42'])
        )
        mock_checksum.assert_called_once_with(
            compress.compressed_filename
        )
        checksum.sha256.assert_called_once_with()
        m_open.return_value.write.assert_called_once_with(
            '{0}  compressed_filename{1}'.format(
                checksum.sha256.return_value, os.linesep
            )
        )

    @patch('kiwi.tasks.result_bundle.Privileges.check_for_root_permissions')
    @patch('kiwi.tasks.result_bundle.Result.load')
    @patch('kiwi.tasks.result_bundle.Command.run')
    @patch('kiwi.tasks.result_bundle.Path.create')
    @patch('kiwi.tasks.result_bundle.Path.which')
    @patch('kiwi.tasks.result_bundle.Path.wipe')
    @patch('kiwi.tasks.result_bundle.Compress')
    @patch('kiwi.tasks.result_bundle.Checksum')
    @patch('os.path.exists')
    @patch('os.chdir')
    @patch('os.unlink')
    @patch('glob.iglob')
    def test_process_result_bundle_as_rpm(
        self, mock_iglob, mock_unlink, mock_chdir, mock_exists, mock_checksum,
        mock_compress, mock_path_wipe, mock_path_which, mock_path_create,
        mock_command, mock_load, mock_Privileges_check_for_root_permissions
    ):
        checksum = Mock()
        compress = Mock()
        mock_path_which.return_value = 'zsyncmake'
        compress.compressed_filename = 'compressed_filename'
        mock_compress.return_value = compress
        mock_checksum.return_value = checksum
        mock_exists.return_value = False
        mock_load.return_value = self.result
        self._init_command_args()
        self.task.command_args['bundle'] = True
        self.task.command_args['--package-as-rpm'] = True
        mock_iglob.return_value = [
            os.sep.join([self.abs_bundle_dir, 'test-image-1.2.3-Build_42'])
        ]

        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.task.process()

        mock_path_wipe.assert_called_once_with(self.abs_bundle_dir)
        mock_Privileges_check_for_root_permissions.assert_called_once_with()
        assert mock_command.call_args_list == [
            call(
                [
                    'cp', 'test-image-1.2.3',
                    os.sep.join(
                        [self.abs_bundle_dir, 'test-image-1.2.3-Build_42']
                    )
                ]
            ),
            call(
                [
                    'rpmbuild', '--nodeps', '--nocheck', '--rmspec', '-bb',
                    os.sep.join([self.abs_bundle_dir, 'test-image.spec'])
                ]
            ),
            call(
                ['bash', '-c', 'mv noarch/*.rpm . && rmdir noarch']
            )
        ]
        mock_chdir.assert_called_once_with(
            self.abs_bundle_dir
        )
        mock_unlink.assert_called_once_with(
            os.sep.join([self.abs_bundle_dir, 'test-image-1.2.3-Build_42'])
        )

    @patch('kiwi.tasks.result_bundle.Result.load')
    @patch('kiwi.tasks.result_bundle.Command.run')
    @patch('kiwi.tasks.result_bundle.Path.create')
    @patch('os.path.exists')
    def test_process_result_bundle_name_includes_version(
        self, mock_exists, mock_path_create, mock_command, mock_load
    ):
        result = Result(self.xml_state)
        result.add(
            key='nameincludesversion', filename='test-1.2.3-image-1.2.3',
            use_for_bundle=True, compress=False, shasum=False
        )

        self.xml_state.xml_data.get_name = Mock(
            return_value='test-1.2.3-image'
        )

        mock_exists.return_value = False
        mock_load.return_value = result
        self._init_command_args()

        self.task.process()

        mock_load.assert_called_once_with(
            os.sep.join([self.abs_target_dir, 'kiwi.result'])
        )
        mock_path_create.assert_called_once_with(self.abs_bundle_dir)
        assert mock_command.call_args_list == [
            call([
                'cp', 'test-1.2.3-image-1.2.3',
                os.sep.join([
                    self.abs_bundle_dir,
                    'test-1.2.3-image-1.2.3-Build_42'
                ])
            ])
        ]

    @patch('kiwi.tasks.result_bundle.Result.load')
    @patch('kiwi.tasks.result_bundle.Command.run')
    @patch('kiwi.tasks.result_bundle.Path.create')
    @patch('kiwi.tasks.result_bundle.Path.which')
    @patch('kiwi.tasks.result_bundle.Compress')
    @patch('kiwi.tasks.result_bundle.Checksum')
    @patch('os.path.exists')
    def test_process_result_bundle_zsyncmake_missing(
        self, mock_exists, mock_checksum, mock_compress,
        mock_path_which, mock_path_create, mock_command, mock_load
    ):
        checksum = Mock()
        compress = Mock()
        mock_path_which.return_value = None
        compress.compressed_filename = 'compressed_filename'
        mock_compress.return_value = compress
        mock_checksum.return_value = checksum
        mock_exists.return_value = False
        mock_load.return_value = self.result
        self._init_command_args()
        self.task.command_args['bundle'] = True
        self.task.command_args['--zsync-source'] = 'http://example.com/zsync'

        with patch('builtins.open'):
            with self._caplog.at_level(logging.WARNING):
                self.task.process()
                assert '--> zsyncmake missing, zsync setup skipped' in \
                    self._caplog.text

    def test_process_result_bundle_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['bundle'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::result::bundle'
        )
