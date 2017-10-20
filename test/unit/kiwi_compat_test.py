import sys

from mock import patch

from .test_helper import argv_kiwi_tests

import kiwi.kiwi_compat


class TestKiwiCompat(object):
    def teardown(self):
        sys.argv = argv_kiwi_tests

    @patch('logging.error')
    def test_compat_mode_invalid_arguments(self, mock_log_error):
        sys.argv = [
            'kiwicompat', '--build'
        ]
        kiwi.kiwi_compat.main()
        assert mock_log_error.called

    @patch('os.execvp')
    @patch('kiwi.kiwi_compat.Path.which')
    @patch('logging.error')
    def test_compat_mode_exec_failed(self, mock_log_error, mock_which, mock_exec):
        mock_which.return_value = 'kiwi-ng'
        sys.argv = [
            'kiwicompat',
            '--create', 'root_dir',
            '--type', 'vmx',
            '-d', 'destination'
        ]
        mock_exec.side_effect = OSError('exec failed')
        kiwi.kiwi_compat.main()
        mock_log_error.assert_called_once_with(
            'KiwiCompatError: %s', 'exec failed'
        )

    @patch('kiwi.kiwi_compat.Path.which')
    @patch('logging.error')
    def test_compat_mode_kiwi_not_found(self, mock_log_error, mock_which):
        mock_which.return_value = None
        sys.argv = [
            'kiwicompat',
            '--create', 'root_dir',
            '--type', 'vmx',
            '-d', 'destination'
        ]
        kiwi.kiwi_compat.main()
        mock_log_error.assert_called_once_with(
            'KiwiCompatError: %s', 'kiwi not found'
        )

    @patch('os.execvp')
    @patch('kiwi.path.Path.which')
    def test_version_compat_mode(self, mock_which, mock_exec):
        mock_which.return_value = 'kiwi-ng'
        sys.argv = [
            'kiwicompat', '--version'
        ]
        kiwi.kiwi_compat.main()
        mock_exec.assert_called_once_with(
            'kiwi-ng', ['kiwi', '--version']
        )

    @patch('os.execvp')
    @patch('kiwi.kiwi_compat.Path.which')
    def test_build_compat_mode(self, mock_which, mock_exec):
        mock_which.return_value = 'kiwi-ng'
        sys.argv = [
            'kiwicompat',
            '--build', 'description',
            '--type', 'vmx',
            '--ignore-repos',
            '--set-repo', 'repo_a',
            '--set-repoalias', 'a', '--set-repopriority', '1',
            '--set-repotype', 'rpm_md',
            '--add-repo', 'repo_b',
            '--add-repoalias', 'b', '--add-repopriority', '2',
            '--add-repotype', 'rpm_md',
            '--add-repo', 'repo_c',
            '--add-repoalias', 'c', '--add-repopriority', '3',
            '--add-repotype', 'rpm_md',
            '--logfile', 'logfile',
            '--add-profile', 'profile',
            '--debug',
            '-d', 'destination'
        ]
        kiwi.kiwi_compat.main()
        mock_exec.assert_called_once_with(
            'kiwi-ng', [
                'kiwi',
                '--logfile', 'logfile',
                '--debug',
                '--type', 'vmx',
                '--profile', 'profile',
                'system', 'build',
                '--description', 'description',
                '--target-dir', 'destination',
                '--ignore-repos',
                '--add-repo', 'repo_b,rpm_md,b,2',
                '--add-repo', 'repo_c,rpm_md,c,3',
                '--set-repo', 'repo_a,rpm_md,a,1'
            ]
        )

    @patch('os.execvp')
    @patch('kiwi.path.Path.which')
    def test_create_compat_mode(self, mock_which, mock_exec):
        mock_which.return_value = 'kiwi-ng'
        sys.argv = [
            'kiwicompat',
            '--create', 'root_dir',
            '--type', 'vmx',
            '-d', 'destination'
        ]
        kiwi.kiwi_compat.main()
        mock_exec.assert_called_once_with(
            'kiwi-ng', [
                'kiwi',
                '--type', 'vmx',
                'system', 'create',
                '--root', 'root_dir',
                '--target-dir', 'destination'
            ]
        )

    @patch('os.execvp')
    @patch('kiwi.path.Path.which')
    def test_prepare_compat_mode(self, mock_which, mock_exec):
        mock_which.return_value = 'kiwi-ng'
        sys.argv = [
            'kiwicompat',
            '--prepare', 'description',
            '--root', 'root_dir',
            '--recycle-root',
            '--ignore-repos',
            '--set-repo', 'repo_a',
            '--set-repoalias', 'a', '--set-repopriority', '1',
            '--set-repotype', 'rpm_md',
            '--add-repo', 'repo_b',
            '--logfile', 'logfile',
            '--add-profile', 'profile',
            '--debug'
        ]
        kiwi.kiwi_compat.main()
        mock_exec.assert_called_once_with(
            'kiwi-ng', [
                'kiwi',
                '--logfile', 'logfile',
                '--debug',
                '--profile', 'profile',
                'system', 'prepare',
                '--description', 'description',
                '--root', 'root_dir',
                '--ignore-repos',
                '--allow-existing-root',
                '--add-repo', 'repo_b,,,',
                '--set-repo', 'repo_a,rpm_md,a,1'
            ]
        )

    @patch('os.execvp')
    @patch('kiwi.path.Path.which')
    def test_upgrade_compat_mode(self, mock_which, mock_exec):
        mock_which.return_value = 'kiwi-ng'
        sys.argv = [
            'kiwicompat',
            '--upgrade', 'root_dir',
            '--add-package', 'foo',
            '--del-package', 'bar'
        ]
        kiwi.kiwi_compat.main()
        mock_exec.assert_called_once_with(
            'kiwi-ng', [
                'kiwi',
                'system', 'update',
                '--root', 'root_dir',
                '--add-package', 'foo',
                '--delete-package', 'bar'
            ]
        )
