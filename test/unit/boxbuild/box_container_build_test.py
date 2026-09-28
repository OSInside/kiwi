from unittest.mock import (
    patch, Mock
)
from pytest import raises

from kiwi.boxbuild.box_container_build import BoxContainerBuild
from kiwi.exceptions import KiwiBoxBuildError


class TestBoxContainerBuild:
    @patch('kiwi.boxbuild.box_container_build.BoxDownload')
    def setup(self, mock_BoxDownload):
        self.box = Mock()
        self.box.fetch_container.return_value = 'some'
        mock_BoxDownload.return_value = self.box
        self.build = BoxContainerBuild(
            boxname='suse', arch='x86_64'
        )

    @patch('kiwi.boxbuild.box_container_build.BoxDownload')
    def setup_method(self, cls, mock_BoxDownload):
        self.setup()

    @patch('os.path.exists')
    @patch('os.environ')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    def test_run_shared_path_does_not_exist(
        self, mock_create_build_target_dir, mock_os_system,
        mock_os_environ, mock_os_path_exists
    ):
        def exists(path):
            if path.endswith('/var/tmp/repos'):
                return False
            return True

        mock_os_path_exists.side_effect = exists
        with raises(KiwiBoxBuildError):
            self.build.run(
                [
                    '--debug', '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', 'target'
                ],
                keep_open=True,
                kiwi_version='9.22.1',
                custom_shared_path='/var/tmp/repos'
            )

    @patch('os.path.exists')
    @patch('os.environ')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    def test_run_image_description_does_not_exist(
        self, mock_create_build_target_dir, mock_os_system,
        mock_os_environ, mock_os_path_exists
    ):
        def exists(path):
            if path.endswith('desc'):
                return False
            return True

        mock_os_path_exists.side_effect = exists
        with raises(KiwiBoxBuildError):
            self.build.run(
                [
                    '--debug', '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', 'target'
                ],
                keep_open=True,
                kiwi_version='9.22.1',
                custom_shared_path='/var/tmp/repos'
            )

    @patch('os.path.isdir')
    @patch('os.path.exists')
    @patch('os.environ')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    @patch('kiwi.boxbuild.box_container_build.NamedTemporaryFile')
    def test_run_build_failed(
        self, mock_NamedTemporaryFile, mock_create_build_target_dir,
        mock_os_system, mock_os_environ, mock_os_path_exists,
        mock_os_path_isdir
    ):
        def exists(path):
            if path.endswith('target/result.code'):
                return True
            if path.endswith('/var/tmp/repos'):
                return True
            if path.endswith('desc'):
                return True
            return False

        mock_os_path_isdir.return_value = True
        mock_os_path_exists.side_effect = exists
        tmpfile = Mock()
        tmpfile.name = 'tmpfile'
        mock_NamedTemporaryFile.return_value = tmpfile
        with patch('builtins.open', create=True) as mock_open:
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.readline.return_value = '1'
            with raises(KiwiBoxBuildError):
                self.build.run(
                    [
                        '--debug', '--type', 'oem', 'system', 'build',
                        '--description', 'desc', '--target-dir', 'target'
                    ],
                    keep_open=True,
                    kiwi_version='9.22.1',
                    custom_shared_path='/var/tmp/repos'
                )

    @patch('os.path.isdir')
    @patch('os.path.abspath')
    @patch('os.path.exists')
    @patch('os.environ')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_container_build.NamedTemporaryFile')
    @patch('kiwi.boxbuild.box_container_build.Command.run')
    def test_run(
        self, mock_Command_run, mock_NamedTemporaryFile,
        mock_os_system, mock_os_environ, mock_os_path_exists,
        mock_os_abspath, mock_os_path_isdir
    ):
        def abspath(path):
            return path

        def exists(path):
            if path == 'target/result.code':
                return True
            if path == '/var/tmp/repos':
                return True
            if path == 'desc':
                return True
            return False

        mock_os_path_isdir.return_value = False
        mock_os_abspath.side_effect = abspath
        mock_os_path_exists.side_effect = exists
        tmpfile = Mock()
        tmpfile.name = 'tmpfile'
        mock_NamedTemporaryFile.return_value = tmpfile
        with patch('builtins.open', create=True) as mock_open:
            file_handle = mock_open.return_value.__enter__.return_value
            file_handle.readline.return_value = '0'
            self.build.run(
                [
                    '--debug', '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', 'target'
                ],
                keep_open=True,
                kiwi_version='9.22.1',
                custom_shared_path='/var/tmp/repos'
            )
        mock_Command_run.assert_called_once_with(
            ['sudo', 'mkdir', '-p', '/var/cache/kiwi']
        )
        mock_os_system.assert_called_once_with(
            'sudo podman run --rm -ti '
            '--privileged '
            '--net host '
            '--cap-add AUDIT_WRITE '
            '--cap-add AUDIT_CONTROL '
            '--cap-add CAP_MKNOD '
            '--cap-add CAP_SYS_ADMIN '
            '--volume /var/cache/kiwi:/var/cache/kiwi '
            '--volume tmpfile:/container.cmdline '
            '--volume target:/bundle '
            '--volume desc:/description '
            '--volume /dev:/dev '
            '--volume /var/tmp/repos:/var/tmp/repos '
            'some'
        )
