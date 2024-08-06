import io
import os
from unittest.mock import (
    patch, call, Mock, MagicMock
)
from pytest import raises

from kiwi.system.uri import Uri
from kiwi.system.root_import.base import RootImportBase

from kiwi.exceptions import KiwiRootImportError


class TestRootImportBase:
    @patch('os.path.exists')
    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_init(self, mock_buildservice, mock_path):
        mock_buildservice.return_value = False
        mock_path.return_value = True
        with patch.dict('os.environ', {'HOME': '../data'}):
            RootImportBase('root_dir', Uri('file:///image.tar.xz'))
        assert call('/image.tar.xz') in mock_path.call_args_list

    def test_init_remote_uri(self):
        with raises(KiwiRootImportError):
            RootImportBase('root_dir', Uri('http://example.com/image.tar.xz'))

    @patch('kiwi.system.root_import.base.log.warning')
    def test_init_unknown_uri(self, mock_log_warn):
        root = RootImportBase('root_dir', Uri('docker://opensuse:leap'))
        assert root.unknown_uri == 'docker://opensuse:leap'
        assert mock_log_warn.called

    @patch('os.path.exists')
    def test_init_non_existing(self, mock_path):
        mock_path.return_value = False
        with patch.dict('os.environ', {'HOME': '../data'}):
            with raises(KiwiRootImportError):
                RootImportBase('root_dir', Uri('file:///image.tar.xz'))

    @patch('os.path.exists')
    def test_data_sync(self, mock_path):
        mock_path.return_value = True
        with patch.dict('os.environ', {'HOME': '../data'}):
            root_import = RootImportBase(
                'root_dir', Uri('file:///image.tar.xz')
            )
        with raises(NotImplementedError):
            root_import.sync_data()

    @patch('os.path.exists')
    def test_overlay_data(self, mock_path):
        mock_path.return_value = True
        with patch.dict('os.environ', {'HOME': '../data'}):
            root_import = RootImportBase(
                'root_dir', Uri('docker://opensuse:leap')
            )
        with raises(NotImplementedError):
            root_import.overlay_data()

    @patch('os.path.exists')
    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    @patch('kiwi.system.root_import.base.SystemSetup')
    @patch('kiwi.system.root_import.base.Path')
    @patch('kiwi.system.root_import.base.pathlib')
    @patch('kiwi.system.root_import.base.Command.run')
    @patch('kiwi.system.uri.RuntimeConfig')
    def test_overlay_finalize(
        self, mock_runtime_config, mock_Command_run, mock_pathlib, mock_Path,
        mock_SystemSetup, mock_buildservice, mock_path_exists
    ):
        mock_path_exists.return_value = True
        mock_buildservice.return_value = False
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            xml_state = Mock()
            mock_Command_run.return_value.output = '/file_a\n/file_b'
            with patch.dict('os.environ', {'HOME': '../data'}):
                root = RootImportBase('root_dir', Uri('docker://opensuse:leap'))
                root.overlay = Mock()
                mock_pathlib.Path = Mock()
                root_overlay_path_mock = Mock()
                mock_pathlib.Path.return_value = root_overlay_path_mock

                root.overlay_finalize(xml_state)

                # run config-overlay.sh
                mock_SystemSetup.return_value.\
                    call_config_overlay_script.assert_called_once_with()

                # run config-host-overlay.sh
                mock_SystemSetup.return_value.\
                    call_config_host_overlay_script.assert_called_once_with(
                        working_directory='root_dir'
                    )

                # umount and create the new upper
                root.overlay.umount.assert_called_once_with()
                assert mock_Path.wipe.call_args_list == [
                    call('root_dir'),
                    call('root_dir_cow_before_pinch'),
                    call(root.overlay.lower),
                    call(root.overlay.work)
                ]

                mock_pathlib.Path.assert_called_once_with(root.overlay.upper)
                root_overlay_path_mock.replace.assert_called_once_with('root_dir')

                # find files that got removed
                assert mock_Command_run.call_args_list == [
                    call(
                        [
                            'rsync', '-av', '--dry-run', '--out-format=%n',
                            '--exclude', 'etc/hosts.kiwi',
                            '--exclude', 'etc/hosts.sha',
                            '--exclude', 'etc/resolv.conf.kiwi',
                            '--exclude', 'etc/resolv.conf.sha',
                            '--exclude', 'etc/sysconfig/proxy.kiwi',
                            '--exclude', 'etc/sysconfig/proxy.sha',
                            '--exclude', 'usr/lib/sysimage/rpm',
                            'root_dir_cow_before_pinch/', 'root_dir/'
                        ]
                    ),
                    call(
                        ['find', 'root_dir', '-type', 'c', '-delete']
                    )
                ]
                # create removed files metadata for later host provisioning
                assert file_handle.write.call_args_list == [
                    call('/file_a'), call(os.linesep),
                    call('/file_b'), call(os.linesep)
                ]
