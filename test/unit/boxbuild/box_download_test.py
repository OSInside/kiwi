from pytest import raises
from unittest.mock import patch, Mock, call

from kiwi.exceptions import (
    KiwiBoxChecksumError,
    KiwiBoxSignatureError,
)
from kiwi.boxbuild.box_download import BoxDownload, vm_setup_type


class TestBoxDownload:
    @patch('kiwi.boxbuild.defaults.BoxBuildDefaults.get_box_config_file')
    @patch('kiwi.boxbuild.box_download.Path')
    @patch('kiwi.boxbuild.box_download.DirFiles')
    def setup(self, mock_DirFiles, mock_Path, mock_get_box_config_file):
        self.box_stage = Mock()
        self.box_stage.register.return_value = 'register_file'
        mock_DirFiles.return_value = self.box_stage
        mock_get_box_config_file.return_value = (
            '../data/boxbuild/kiwi_boxed_plugin.yml'
        )
        with patch.dict('os.environ', {'HOME': 'HOME'}):
            self.box = BoxDownload('suse', 'x86_64')
        mock_Path.create.assert_called_once_with('HOME/.kiwi_boxes/suse')
        self.result = vm_setup_type(
            system='HOME/.kiwi_boxes/suse/'
            'SUSE-Box.x86_64-1.42.1-System-BuildBox.qcow2',
            kernel='HOME/.kiwi_boxes/suse/kernel.x86_64',
            initrd='HOME/.kiwi_boxes/suse/initrd.x86_64',
            append='console=hvc0 root=/dev/vda1 rd.plymouth=0',
            console='hvc0',
            ram='8096M',
            smp=4,
        )

    @patch('kiwi.boxbuild.defaults.BoxBuildDefaults.get_box_config_file')
    @patch('kiwi.boxbuild.box_download.Path')
    @patch('kiwi.boxbuild.box_download.DirFiles')
    def setup_method(
        self, cls, mock_DirFiles, mock_Path, mock_get_box_config_file
    ):
        self.setup()

    @patch('kiwi.boxbuild.defaults.BoxBuildDefaults.get_box_config_file')
    @patch('kiwi.boxbuild.box_download.Path')
    @patch('kiwi.boxbuild.box_download.DirFiles')
    @patch('os.path.isdir')
    def test_custom_box_cache_dir(
        self,
        mock_os_path_isdir,
        mock_DirFiles,
        mock_Path,
        mock_get_box_config_file,
    ):
        mock_os_path_isdir.return_value = True
        mock_DirFiles.return_value = Mock().register.return_value = (
            'register_file'
        )
        mock_get_box_config_file.return_value = (
            '../data/boxbuild/kiwi_boxed_plugin.yml'
        )
        with patch.dict(
            'os.environ', {'KIWI_BOXED_CACHE_DIR': '/some/custom/dir'}
        ):
            BoxDownload('suse', 'x86_64')
        mock_Path.create.assert_called_once_with('/some/custom/dir/suse')

    BOX_DIR = 'HOME/.kiwi_boxes/suse'
    KERNEL = 'SUSE-Box.x86_64-1.42.1-Kernel-BuildBox.tar.xz'
    SYSTEM = 'SUSE-Box.x86_64-1.42.1-System-BuildBox.qcow2'
    PACKAGES = 'SUSE-Box.x86_64-1.42.1-System-BuildBox.report'
    CHECKSUM_FILES = [f'{KERNEL}.sha256', f'{SYSTEM}.sha256']
    DOWNLOAD_FILES = [
        KERNEL,
        SYSTEM,
        f'{KERNEL}.sha256',
        f'{SYSTEM}.sha256',
        f'{KERNEL}.sha256.asc',
        f'{SYSTEM}.sha256.asc',
    ]

    def _fetch(
        self,
        update_check=True,
        snapshot=True,
        files_exist=True,
        packages_changed=False,
        verify_error=None,
    ):
        """
        Run fetch with all external operations mocked. The box files
        exist in the cache if files_exist is set, the packages file
        of the box changed if packages_changed is set. Staged files
        are named after the file in the cache with a .tmp suffix
        """
        self.box_stage.register.side_effect = lambda name: f'{name}.tmp'
        checksum = Mock()
        checksum.sha256.return_value = 'sum'
        checksum.matches.return_value = not packages_changed
        repo = Mock()
        repo._get_mime_typed_uri.return_value = 'uri://'
        self.fetcher = Mock()
        self.verified_checksums = {'some': 'sum'}
        with patch(
            'kiwi.boxbuild.box_download.FetchFiles',
            return_value=self.fetcher,
        ), patch(
            'kiwi.boxbuild.box_download.SolverRepository.new',
            return_value=repo,
        ), patch(
            'kiwi.boxbuild.box_download.Uri'
        ), patch(
            'kiwi.boxbuild.box_download.Checksum', return_value=checksum
        ), patch(
            'os.path.exists', return_value=files_exist
        ), patch(
            'os.unlink'
        ) as self.mock_unlink, patch(
            'kiwi.boxbuild.box_download.Command.run'
        ) as self.mock_Command_run, patch.object(
            BoxDownload,
            '_get_verified_checksums',
            return_value=self.verified_checksums,
        ) as self.mock_get_verified_checksums, patch.object(
            BoxDownload, '_verify_checksum', side_effect=verify_error
        ) as self.mock_verify_checksum, patch(
            'builtins.open', create=True
        ):
            with patch.dict('os.environ', {'HOME': 'HOME'}):
                return self.box.fetch(
                    update_check=update_check, snapshot=snapshot
                )

    def _verified_box_files(self):
        return [
            verify_call.args[0]
            for verify_call in self.mock_verify_checksum.call_args_list
        ]

    def test_fetch_download(self):
        assert self._fetch(packages_changed=True) == self.result
        # box files, checksum files and their signatures are downloaded
        assert self.fetcher.wget.call_args_list == [
            call(
                url=f'uri:///{name}',
                filename=f'{self.BOX_DIR}/{name}.tmp',
            )
            for name in self.DOWNLOAD_FILES
        ]
        # the downloaded files are verified before they are committed
        local_files = {
            name: f'{self.BOX_DIR}/{name}.tmp' for name in self.DOWNLOAD_FILES
        }
        self.mock_get_verified_checksums.assert_called_once_with(
            self.CHECKSUM_FILES, local_files
        )
        assert self.mock_verify_checksum.call_args_list == [
            call(name, f'{self.BOX_DIR}/{name}.tmp', self.verified_checksums)
            for name in (self.KERNEL, self.SYSTEM)
        ]
        self.box_stage.commit.assert_called_once_with()
        # the kernel and initrd are extracted from the cache
        assert [
            run_call.args[0][-2]
            for run_call in self.mock_Command_run.call_args_list
        ] == [f'{self.BOX_DIR}/{self.KERNEL}', f'{self.BOX_DIR}/{self.KERNEL}']

    def test_fetch_download_missing_files_without_update_check(self):
        # files missing in the cache are downloaded and verified
        # also if no update check is requested
        assert self._fetch(update_check=False, files_exist=False) == (
            self.result
        )
        assert len(self.fetcher.wget.call_args_list) == 6
        assert self._verified_box_files() == [self.KERNEL, self.SYSTEM]
        self.box_stage.commit.assert_called_once_with()

    def test_fetch_download_without_snapshot(self):
        # a downloaded system image is verified, also if it is not
        # used in snapshot mode
        self._fetch(snapshot=False, packages_changed=True)
        assert self._verified_box_files() == [self.KERNEL, self.SYSTEM]

    def test_fetch_download_verification_failed(self):
        with raises(KiwiBoxChecksumError):
            self._fetch(
                packages_changed=True,
                verify_error=KiwiBoxChecksumError('Checksum failed'),
            )
        # the box files in the cache are not replaced and the
        # downloaded files are deleted
        assert not self.box_stage.commit.called
        assert sorted(
            unlink_call.args[0]
            for unlink_call in self.mock_unlink.call_args_list
        ) == sorted(
            f'{self.BOX_DIR}/{name}.tmp' for name in self.DOWNLOAD_FILES
        )

    def test_fetch_cached(self):
        assert self._fetch() == self.result
        assert not self.fetcher.wget.called
        assert not self.box_stage.commit.called
        # the box files from the cache are verified
        local_files = {
            name: f'{self.BOX_DIR}/{name}' for name in self.DOWNLOAD_FILES
        }
        self.mock_get_verified_checksums.assert_called_once_with(
            self.CHECKSUM_FILES, local_files
        )
        assert self.mock_verify_checksum.call_args_list == [
            call(name, f'{self.BOX_DIR}/{name}', self.verified_checksums)
            for name in (self.KERNEL, self.SYSTEM)
        ]

    def test_fetch_cached_without_snapshot(self):
        # the system image changes when it is not used in snapshot
        # mode, it can't be verified from the cache
        self._fetch(snapshot=False)
        assert self._verified_box_files() == [self.KERNEL]

    def test_fetch_cached_update_check_disabled(self):
        assert self._fetch(update_check=False) == self.result
        assert not self.fetcher.wget.called
        assert not self.mock_get_verified_checksums.called
        assert not self.mock_verify_checksum.called

    @patch('kiwi.boxbuild.box_download.BoxBuildDefaults.get_box_keyring_file')
    @patch('kiwi.boxbuild.box_download.Command.run')
    def test_get_verified_checksums(
        self, mock_Command_run, mock_get_box_keyring_file, tmp_path
    ):
        mock_get_box_keyring_file.return_value = '/etc/kiwi_boxed_plugin.gpg'
        mock_Command_run.return_value = Mock(returncode=0)
        kernel_sums = tmp_path / 'kernel.sha256'
        kernel_sums.write_text(f'aaa  {self.KERNEL}\n')
        # a checksum file of a manual build, created by sha256sum for
        # more than one file, in binary mode and with a path
        system_sums = tmp_path / 'system.sha256'
        system_sums.write_text(f'bbb *build/{self.SYSTEM}\nccc  other.file\n\n')
        local_files = {
            f'{self.KERNEL}.sha256': str(kernel_sums),
            f'{self.KERNEL}.sha256.asc': 'kernel.asc',
            f'{self.SYSTEM}.sha256': str(system_sums),
            f'{self.SYSTEM}.sha256.asc': 'system.asc',
        }
        assert self.box._get_verified_checksums(
            self.CHECKSUM_FILES, local_files
        ) == {self.KERNEL: 'aaa', self.SYSTEM: 'bbb', 'other.file': 'ccc'}
        assert mock_Command_run.call_args_list == [
            call(
                [
                    'sqv',
                    '--keyring',
                    '/etc/kiwi_boxed_plugin.gpg',
                    'kernel.asc',
                    str(kernel_sums),
                ],
                raise_on_error=False,
            ),
            call(
                [
                    'sqv',
                    '--keyring',
                    '/etc/kiwi_boxed_plugin.gpg',
                    'system.asc',
                    str(system_sums),
                ],
                raise_on_error=False,
            ),
        ]

    @patch('kiwi.boxbuild.box_download.Command.run')
    def test_get_verified_checksums_bad_signature(self, mock_Command_run):
        mock_Command_run.return_value = Mock(
            returncode=1, error='Message has been manipulated'
        )
        with raises(KiwiBoxSignatureError) as issue:
            self.box._get_verified_checksums(
                ['box.sha256'],
                {'box.sha256': 'box.sha256', 'box.sha256.asc': 'box.asc'},
            )
        assert format(issue.value) == (
            'Signature verification failed for box.sha256: '
            'Message has been manipulated'
        )

    @patch('kiwi.boxbuild.box_download.Checksum')
    def test_verify_checksum(self, mock_Checksum):
        mock_Checksum.return_value.sha256.return_value = 'aaa'
        self.box._verify_checksum('box.qcow2', 'local', {'box.qcow2': 'aaa'})
        mock_Checksum.assert_called_once_with('local')
        with raises(KiwiBoxChecksumError) as issue:
            self.box._verify_checksum('box.qcow2', 'local', {'box.qcow2': 'b'})
        assert format(issue.value) == 'Checksum failed for box.qcow2'
        with raises(KiwiBoxChecksumError) as issue:
            self.box._verify_checksum('box.qcow2', 'local', {'other': 'aaa'})
        assert format(issue.value) == (
            'No checksum for box.qcow2 found in the box checksum files'
        )

    @patch('os.system')
    def test_fetch_container(self, mock_os_system):
        assert self.box.fetch_container() == 'some'
        mock_os_system.assert_called_once_with('sudo podman pull some')
