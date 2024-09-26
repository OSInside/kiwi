import os
import sys
import logging
from unittest.mock import (
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

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['bundle'] = False
        self.task.command_args['--target-dir'] = 'target_dir'
        self.task.command_args['--bundle-dir'] = 'bundle_dir'
        self.task.command_args['--id'] = 'Build_42'
        self.task.command_args['--zsync-source'] = None
        self.task.command_args['--package-as-rpm'] = None
        self.task.command_args['--bundle-format'] = None

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
    @patch('os.path.islink')
    @patch('os.unlink')
    @patch('os.symlink')
    @patch('os.readlink')
    def test_process_result_bundle(
        self, mock_os_readlink, mock_os_symlink, mock_os_unlink,
        mock_os_path_islink, mock_exists, mock_checksum, mock_compress,
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
        compress.xz.return_value = 'compressed_filename'
        mock_compress.return_value = compress
        mock_checksum.return_value = checksum
        mock_exists.return_value = False
        mock_load.return_value = self.result
        self._init_command_args()
        self.task.command_args['bundle'] = True
        self.task.command_args['--zsync-source'] = 'http://example.com/zsync'

        command_result = Mock()
        command_result.output = "some mime is text"
        mock_command.return_value = command_result

        mock_os_readlink.return_value = 'readlinked'

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
                'cp', 'test-image-noversion',
                os.sep.join([self.abs_bundle_dir, 'test-image-noversion'])
            ]),
            call([
                'file',
                os.sep.join([self.abs_bundle_dir, 'test-image-1.2.3-Build_42'])
            ]),
            call([
                'sed', '-ie', 's/test-image-1.2.3/readlinked/g',
                os.sep.join([self.abs_bundle_dir, 'test-image-1.2.3-Build_42'])
            ]),
            call([
                'file',
                os.sep.join([self.abs_bundle_dir, 'test-image-noversion'])
            ]),
            call([
                'sed', '-ie', 's/test-image-1.2.3/readlinked/g',
                os.sep.join([self.abs_bundle_dir, 'test-image-noversion'])
            ]),
            call([
                'zsyncmake', '-e',
                '-u', 'http://example.com/zsync/compressed_filename',
                '-o', 'compressed_filename.zsync',
                'compressed_filename'
            ])
        ]
        mock_compress.assert_called_once_with(
            os.sep.join([self.abs_bundle_dir, 'test-image-1.2.3-Build_42'])
        )
        mock_checksum.assert_called_once_with(
            'compressed_filename'
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
    @patch('os.path.islink')
    @patch('os.symlink')
    @patch('os.readlink')
    @patch('os.path.realpath')
    @patch('os.path.abspath')
    def test_process_result_bundle_as_rpm(
        self, mock_os_path_abspath, mock_os_path_realpath, mock_os_readlink,
        mock_os_symlink, mock_os_path_islink, mock_iglob, mock_unlink,
        mock_chdir, mock_exists, mock_checksum, mock_compress,
        mock_path_wipe, mock_path_which, mock_path_create, mock_command,
        mock_load, mock_Privileges_check_for_root_permissions
    ):
        def abspath(path):
            if path == 'target_dir':
                return 'target-dir'
            else:
                return 'bundle-dir'

        checksum = Mock()
        compress = Mock()
        mock_os_readlink.return_value = 'readlink'
        mock_os_path_abspath.side_effect = abspath
        mock_path_which.return_value = 'zsyncmake'
        compress.xz.return_value = 'compressed_filename'
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

        mock_path_wipe.assert_called_once_with('bundle-dir')
        mock_Privileges_check_for_root_permissions.assert_called_once_with()
        assert mock_command.call_args_list == [
            call(
                [
                    'cp', 'test-image-1.2.3',
                    os.sep.join(
                        ['bundle-dir', 'test-image-1.2.3-Build_42']
                    )
                ]
            ),
            call(
                [
                    'file',
                    os.sep.join(
                        ['bundle-dir', 'test-image-1.2.3-Build_42']
                    )
                ]
            ),
            call(
                [
                    'rpmbuild', '--nodeps', '--nocheck', '--rmspec', '-bb',
                    os.sep.join(['bundle-dir', 'test-image.spec'])
                ]
            ),
            call(
                ['bash', '-c', 'mv noarch/*.rpm . && rmdir noarch']
            )
        ]
        mock_chdir.assert_called_once_with('bundle-dir')
        assert mock_unlink.called

    @patch('kiwi.tasks.result_bundle.Result.load')
    @patch('kiwi.tasks.result_bundle.Command.run')
    @patch('kiwi.tasks.result_bundle.Path.create')
    @patch('os.path.exists')
    @patch('os.path.islink')
    @patch('os.unlink')
    @patch('os.symlink')
    @patch('os.readlink')
    def test_process_result_bundle_with_bundle_format(
        self, mock_os_readlink, mock_os_symlink, mock_os_unlink,
        mock_os_path_islink, mock_exists, mock_path_create, mock_command,
        mock_load
    ):
        self.xml_state.profiles = None
        self.xml_state.host_architecture = 'x86_64'
        self.xml_state.get_build_type_name = Mock(
            return_value='oem'
        )
        self.xml_state.xml_data.get_name = Mock(
            return_value='Leap-15.2'
        )

        result = Result(self.xml_state)
        result.add_bundle_format('%N-%T:%M')
        result.add(
            key='disk_image',
            filename='/tmp/mytest/Leap-15.2.x86_64-1.15.2.raw',
            use_for_bundle=True, compress=False, shasum=False
        )

        mock_exists.return_value = False
        mock_load.return_value = result
        self._init_command_args()

        self.task.process()

        assert mock_command.call_args_list == [
            call(
                [
                    'cp',
                    '/tmp/mytest/Leap-15.2.x86_64-1.15.2.raw',
                    os.sep.join(
                        [self.abs_bundle_dir, 'Leap-15.2-oem:1.raw']
                    )
                ]
            ),
            call(
                [
                    'file',
                    os.sep.join(
                        [self.abs_bundle_dir, 'Leap-15.2-oem:1.raw']
                    )
                ]
            )
        ]

    @patch('kiwi.tasks.result_bundle.Result.load')
    @patch('kiwi.tasks.result_bundle.Command.run')
    @patch('kiwi.tasks.result_bundle.Path.create')
    @patch('os.path.exists')
    @patch('os.path.islink')
    @patch('os.unlink')
    @patch('os.symlink')
    @patch('os.readlink')
    def test_process_result_bundle_with_bundle_format_for_vagrant_types(
        self, mock_os_readlink, mock_os_symlink, mock_os_unlink,
        mock_os_path_islink, mock_exists, mock_path_create, mock_command,
        mock_load
    ):
        self.xml_state.profiles = None
        self.xml_state.host_architecture = 'x86_64'
        self.xml_state.get_build_type_name = Mock(
            return_value='oem'
        )
        self.xml_state.xml_data.get_name = Mock(
            return_value='Leap-15.2'
        )

        result = Result(self.xml_state)
        result.add_bundle_format('%N-%T:%M')
        result.add(
            key='disk_image',
            filename='/tmp/mytest/Leap-15.2.x86_64-1.15.2.vagrant.virtualbox.box',
            use_for_bundle=True, compress=False, shasum=False
        )

        mock_exists.return_value = False
        mock_load.return_value = result
        self._init_command_args()

        self.task.process()

        assert mock_command.call_args_list == [
            call(
                [
                    'cp',
                    '/tmp/mytest/Leap-15.2.x86_64-1.15.2.vagrant.virtualbox.box',
                    os.sep.join(
                        [self.abs_bundle_dir, 'Leap-15.2-oem:1.vagrant.virtualbox.box']
                    )
                ]
            ),
            call(
                [
                    'file',
                    os.sep.join(
                        [self.abs_bundle_dir, 'Leap-15.2-oem:1.vagrant.virtualbox.box']
                    )
                ]
            )
        ]

    @patch('kiwi.tasks.result_bundle.Result.load')
    @patch('kiwi.tasks.result_bundle.Command.run')
    @patch('kiwi.tasks.result_bundle.Path.create')
    @patch('os.path.exists')
    @patch('os.path.islink')
    @patch('os.unlink')
    @patch('os.symlink')
    @patch('os.readlink')
    def test_process_result_bundle_with_bundle_format_for_archive_types(
        self, mock_os_readlink, mock_os_symlink, mock_os_unlink,
        mock_os_path_islink, mock_exists, mock_path_create, mock_command,
        mock_load
    ):
        self.xml_state.profiles = None
        self.xml_state.host_architecture = 'x86_64'
        self.xml_state.get_build_type_name = Mock(
            return_value='oem'
        )
        self.xml_state.xml_data.get_name = Mock(
            return_value='Leap-15.2'
        )

        result = Result(self.xml_state)
        result.add_bundle_format('%N-%T:%M')
        result.add(
            key='disk_image',
            filename='/tmp/mytest/Leap-15.2.x86_64-1.15.2.tar.xz',
            use_for_bundle=True, compress=False, shasum=False
        )

        mock_exists.return_value = False
        mock_load.return_value = result
        self._init_command_args()

        self.task.process()

        assert mock_command.call_args_list == [
            call(
                [
                    'cp',
                    '/tmp/mytest/Leap-15.2.x86_64-1.15.2.tar.xz',
                    os.sep.join(
                        [self.abs_bundle_dir, 'Leap-15.2-oem:1.tar.xz']
                    )
                ]
            ),
            call(
                [
                    'file',
                    os.sep.join(
                        [self.abs_bundle_dir, 'Leap-15.2-oem:1.tar.xz']
                    )
                ]
            )
        ]

    @patch('kiwi.tasks.result_bundle.Result.load')
    @patch('kiwi.tasks.result_bundle.Command.run')
    @patch('kiwi.tasks.result_bundle.Path.create')
    @patch('os.path.exists')
    @patch('os.path.islink')
    @patch('os.unlink')
    @patch('os.symlink')
    @patch('os.readlink')
    def test_process_result_bundle_with_bundle_format_from_commandline(
        self, mock_os_readlink, mock_os_symlink, mock_os_unlink,
        mock_os_path_islink, mock_exists, mock_path_create, mock_command,
        mock_load
    ):
        self.xml_state.profiles = None
        self.xml_state.host_architecture = 'x86_64'
        self.xml_state.get_build_type_name = Mock(
            return_value='oem'
        )
        self.xml_state.xml_data.get_name = Mock(
            return_value='Leap-15.2'
        )

        result = Result(self.xml_state)
        result.add(
            key='disk_image',
            filename='/tmp/mytest/Leap-15.2.x86_64-1.15.2.raw',
            use_for_bundle=True, compress=False, shasum=False
        )

        mock_exists.return_value = False
        mock_load.return_value = result
        self._init_command_args()

        self.task.command_args['--bundle-format'] = '%N-%T:%M'

        self.task.process()

        assert mock_command.call_args_list == [
            call(
                [
                    'cp',
                    '/tmp/mytest/Leap-15.2.x86_64-1.15.2.raw',
                    os.sep.join(
                        [self.abs_bundle_dir, 'Leap-15.2-oem:1.raw']
                    )
                ]
            ),
            call(
                [
                    'file',
                    os.sep.join(
                        [self.abs_bundle_dir, 'Leap-15.2-oem:1.raw']
                    )
                ]
            )
        ]

    @patch('kiwi.tasks.result_bundle.Result.load')
    @patch('kiwi.tasks.result_bundle.Command.run')
    @patch('kiwi.tasks.result_bundle.Path.create')
    @patch('os.path.exists')
    @patch('os.path.islink')
    @patch('os.unlink')
    @patch('os.symlink')
    @patch('os.readlink')
    def test_process_result_bundle_name_includes_version(
        self, mock_os_readlink, mock_os_symlink, mock_os_unlink,
        mock_os_path_islink, mock_exists, mock_path_create, mock_command,
        mock_load
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
            call(
                [
                    'cp', 'test-1.2.3-image-1.2.3',
                    os.sep.join(
                        [self.abs_bundle_dir, 'test-1.2.3-image-1.2.3-Build_42']
                    )
                ]
            ),
            call(
                [
                    'file',
                    os.sep.join(
                        [self.abs_bundle_dir, 'test-1.2.3-image-1.2.3-Build_42']
                    )
                ]
            )
        ]

    @patch('kiwi.tasks.result_bundle.Result.load')
    @patch('kiwi.tasks.result_bundle.Command.run')
    @patch('kiwi.tasks.result_bundle.Path.create')
    @patch('kiwi.tasks.result_bundle.Path.which')
    @patch('kiwi.tasks.result_bundle.Compress')
    @patch('kiwi.tasks.result_bundle.Checksum')
    @patch('os.path.exists')
    @patch('os.path.islink')
    @patch('os.unlink')
    @patch('os.symlink')
    @patch('os.readlink')
    def test_process_result_bundle_zsyncmake_missing(
        self, mock_os_readlink, mock_os_symlink, mock_os_unlink,
        mock_os_path_islink, mock_exists, mock_checksum, mock_compress,
        mock_path_which, mock_path_create, mock_command, mock_load
    ):
        checksum = Mock()
        compress = Mock()
        mock_path_which.return_value = None
        compress.xz.return_value = 'compressed_filename'
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
