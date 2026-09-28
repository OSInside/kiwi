from unittest.mock import (
    patch, Mock, call
)
from pytest import raises

from kiwi.boxbuild.box_build import BoxBuild
import kiwi.boxbuild.defaults as defaults

from kiwi.exceptions import (
    KiwiBoxDownloadError,
    KiwiBoxVirtioFsError,
    KiwiBoxQEMUBinaryNotFound,
    KiwiBoxSSHPortInvalid,
    KiwiBoxSSHKeyNotFound,
    KiwiBoxBuildError
)


class TestBoxBuild:
    @patch('kiwi.boxbuild.box_build.BoxDownload')
    def setup(self, mock_BoxDownload):
        self.box = Mock()
        self.vm_setup = Mock()
        self.vm_setup.kernel = 'kernel'
        self.vm_setup.append = 'console=hvc0'
        self.vm_setup.system = 'system'
        self.vm_setup.initrd = 'initrd'
        self.vm_setup.console = 'hvc0'
        self.vm_setup.ram = 4096
        self.vm_setup.smp = 4
        self.box.fetch.return_value = self.vm_setup
        mock_BoxDownload.return_value = self.box
        self.build = BoxBuild(
            boxname='suse', arch='x86_64'
        )
        self.build_arm = BoxBuild(
            boxname='universal', arch='aarch64',
            machine='virt', cpu='cortex-a57',
            console='ttyAMA0'
        )

    @patch('kiwi.boxbuild.box_build.BoxDownload')
    def setup_method(self, cls, mock_BoxDownload):
        self.setup()

    @patch('os.environ')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    @patch('kiwi.boxbuild.box_build.Path.which')
    def test_raises_on_kiwi_error(
        self, mock_path_which, mock_create_build_target_dir,
        mock_os_system, mock_os_environ
    ):
        mock_path_which.return_value = 'qemu-system-x86_64'
        with raises(KiwiBoxBuildError):
            self.build.run(
                [
                    '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', '../data/boxbuild/target'
                ]
            )

    @patch('os.environ')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    @patch('kiwi.boxbuild.box_build.Path.which')
    def test_raises_on_invalid_ssh_port(
        self, mock_path_which, mock_create_build_target_dir,
        mock_os_system, mock_os_environ
    ):
        mock_path_which.return_value = 'qemu-system-x86_64'
        self.build.ssh_port = 'bogus'
        with raises(KiwiBoxSSHPortInvalid):
            self.build.run(
                [
                    '--debug', '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', 'target'
                ]
            )

    @patch('os.environ')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    @patch('kiwi.boxbuild.box_build.Path.which')
    def test_raises_on_download_error(
        self, mock_path_which, mock_create_build_target_dir,
        mock_os_system, mock_os_environ
    ):
        mock_path_which.return_value = 'qemu-system-x86_64'
        self.box.fetch.side_effect = Exception('error')
        with raises(KiwiBoxDownloadError):
            self.build.run(
                [
                    '--debug', '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', 'target'
                ]
            )

    @patch('os.environ')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    @patch('kiwi.boxbuild.box_build.Path.which')
    def test_run_with_9p_sharing(
        self, mock_path_which, mock_create_build_target_dir,
        mock_os_system, mock_os_environ
    ):
        mock_path_which.return_value = 'qemu-system-x86_64'
        self.build.run(
            [
                '--debug', '--type', 'oem', 'system', 'build',
                '--description', 'desc', '--target-dir', 'target'
            ],
            keep_open=True,
            kiwi_version='9.22.1',
            custom_shared_path='/var/tmp/repos'
        )
        mock_create_build_target_dir.assert_called_once_with('target')
        mock_os_system.assert_called_once_with(
            'qemu-system-x86_64 '
            '-m 4096 '
            '-accel accel=kvm '
            '-cpu host '
            '-nographic '
            '-nodefaults '
            '-snapshot '
            '-kernel kernel '
            '-append "console=hvc0 kiwi=\\"--debug --type oem system build\\"'
            ' kiwi-no-halt kiwi_version=_9.22.1_'
            ' custom_mount=_/var/tmp/repos_'
            ' sharing_backend=_9p_" '
            '-drive file=system,if=virtio,driver=qcow2,cache=off,snapshot=on '
            '-nic user,model=virtio,hostfwd=tcp::10022-:22 '
            '-device virtio-serial '
            '-chardev stdio,id=virtiocon0 '
            '-device virtconsole,chardev=virtiocon0 '
            '-fsdev local,security_model=mapped,id=fsdev0,path=desc '
            '-device virtio-9p-pci,id=fs0,fsdev=fsdev0,mount_tag='
            'kiwidescription '
            '-fsdev local,security_model=mapped,id=fsdev1,path=target '
            '-device virtio-9p-pci,id=fs1,fsdev=fsdev1,mount_tag='
            'kiwibundle '
            '-fsdev local,security_model=mapped,id=fsdev2,path=/var/tmp/repos '
            '-device virtio-9p-pci,id=fs2,fsdev=fsdev2,mount_tag='
            'custompath '
            '-initrd initrd '
            '-smp 4'
        )

    @patch('os.environ')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    @patch('kiwi.boxbuild.box_build.Path.which')
    def test_run_cross_arch_aarch64_on_x86_64(
        self, mock_path_which, mock_create_build_target_dir,
        mock_os_system, mock_os_environ
    ):
        mock_path_which.return_value = 'qemu-system-aarch64'
        self.build_arm.run(
            [
                '--type', 'oem', 'system', 'build',
                '--description', 'desc', '--target-dir', 'target'
            ],
            keep_open=True,
            kiwi_version='9.22.1',
            custom_shared_path='/var/tmp/repos'
        )
        mock_create_build_target_dir.assert_called_once_with('target')
        mock_os_system.assert_called_once_with(
            'qemu-system-aarch64 '
            '-m 4096 '
            '-machine virt '
            '-accel accel=kvm '
            '-cpu cortex-a57 '
            '-nographic '
            '-nodefaults '
            '-snapshot '
            '-kernel kernel '
            '-append "console=ttyAMA0 kiwi=\\"--type oem system build\\"'
            ' kiwi-no-halt kiwi_version=_9.22.1_'
            ' custom_mount=_/var/tmp/repos_'
            ' sharing_backend=_9p_" '
            '-drive file=system,if=virtio,driver=qcow2,cache=off,snapshot=on '
            '-nic user,model=virtio,hostfwd=tcp::10022-:22 '
            '-device virtio-serial '
            '-chardev stdio,id=virtiocon0 '
            '-device virtconsole,chardev=virtiocon0 '
            '-fsdev local,security_model=mapped,id=fsdev0,path=desc '
            '-device virtio-9p-pci,id=fs0,fsdev=fsdev0,mount_tag='
            'kiwidescription '
            '-fsdev local,security_model=mapped,id=fsdev1,path=target '
            '-device virtio-9p-pci,id=fs1,fsdev=fsdev1,mount_tag='
            'kiwibundle '
            '-fsdev local,security_model=mapped,id=fsdev2,path=/var/tmp/repos '
            '-device virtio-9p-pci,id=fs2,fsdev=fsdev2,mount_tag='
            'custompath '
            '-initrd initrd '
            '-smp 4'
        )

    @patch('os.environ')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    @patch('kiwi.boxbuild.box_build.Path.which')
    def test_run_raises_no_qemu_binary_found(
        self, mock_path_which, mock_create_build_target_dir,
        mock_os_system, mock_os_environ
    ):
        mock_path_which.return_value = None
        with raises(KiwiBoxQEMUBinaryNotFound):
            self.build.run(
                [
                    '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', 'target'
                ],
                keep_open=True,
                kiwi_version='9.22.1',
                custom_shared_path='/var/tmp/repos'
            )
        with raises(KiwiBoxQEMUBinaryNotFound):
            self.build_arm.run(
                [
                    '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', 'target'
                ]
            )

    @patch('os.environ')
    @patch('os.system')
    @patch('subprocess.Popen')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    @patch('kiwi.boxbuild.defaults.Path.which')
    def test_run_with_virtiofs_sharing_raises(
        self, mock_path_which, mock_create_build_target_dir,
        mock_subprocess_Popen, mock_os_system, mock_os_environ
    ):
        path_which_results = [None, 'qemu-system-x86_64']

        def path_which(name, lookup=None):
            return path_which_results.pop()

        mock_path_which.side_effect = path_which

        self.build.sharing_backend = 'virtiofs'
        with raises(KiwiBoxVirtioFsError):
            self.build.run(
                [
                    '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', 'target'
                ]
            )

        path_which_results = ['virtiofsd', 'qemu-system-x86_64']
        mock_subprocess_Popen.side_effect = Exception
        with raises(KiwiBoxVirtioFsError):
            self.build.run(
                [
                    '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', 'target'
                ]
            )

    @patch('os.environ')
    @patch('os.system')
    @patch('os.path.abspath')
    @patch('subprocess.Popen')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    @patch('kiwi.boxbuild.defaults.Path.which')
    def test_run_with_virtiofs_sharing(
        self, mock_path_which, mock_create_build_target_dir,
        mock_subprocess_Popen, mock_os_path_abspath, mock_os_system,
        mock_os_environ
    ):
        def abs_path(arg):
            return 'abspath/{0}'.format(arg)

        def new_process(self, **args):
            return Mock()

        def path_which(name, lookup=None):
            if name == 'qemu-system-x86_64':
                return 'qemu-system-x86_64'
            elif name == 'virtiofsd':
                return '/usr/libexec/virtiofsd'

        mock_path_which.side_effect = path_which
        mock_os_path_abspath.side_effect = abs_path
        mock_subprocess_Popen.side_effect = new_process
        self.build.sharing_backend = 'virtiofs'
        self.build.run(
            [
                '--type', 'oem', 'system', 'build',
                '--description', 'desc', '--target-dir', 'target'
            ],
            keep_open=True,
            kiwi_version='9.22.1',
            custom_shared_path='var/tmp/repos'
        )
        mock_create_build_target_dir.assert_called_once_with('target')
        mock_os_system.assert_called_once_with(
            'qemu-system-x86_64 '
            '-m 4096 '
            '-accel accel=kvm '
            '-cpu host '
            '-nographic '
            '-nodefaults '
            '-snapshot '
            '-kernel kernel '
            '-append "console=hvc0 kiwi=\\"--type oem system build\\"'
            ' kiwi-no-halt kiwi_version=_9.22.1_'
            ' custom_mount=_var/tmp/repos_'
            ' sharing_backend=_virtiofs_" '
            '-drive file=system,if=virtio,driver=qcow2,cache=off,snapshot=on '
            '-nic user,model=virtio,hostfwd=tcp::10022-:22 '
            '-device virtio-serial '
            '-chardev stdio,id=virtiocon0 '
            '-device virtconsole,chardev=virtiocon0 '
            '-chardev socket,id=char0,path=/tmp/vhostqemu_0 '
            '-device vhost-user-fs-pci,queue-size=1024,chardev=char0,tag='
            'kiwidescription '
            '-chardev socket,id=char1,path=/tmp/vhostqemu_1 '
            '-device vhost-user-fs-pci,queue-size=1024,chardev=char1,tag='
            'kiwibundle '
            '-chardev socket,id=char2,path=/tmp/vhostqemu_2 '
            '-device vhost-user-fs-pci,queue-size=1024,chardev=char2,tag='
            'custompath '
            '-object '
            'memory-backend-file,id=mem,size=4096,mem-path=/dev/shm,share=on '
            '-numa node,memdev=mem '
            '-initrd initrd '
            '-smp 4'
        )
        assert mock_subprocess_Popen.call_args_list == [
            call(
                [
                    '/usr/libexec/virtiofsd',
                    '--socket-path=/tmp/vhostqemu_0',
                    '--shared-dir', 'abspath/desc',
                    '--sandbox', 'namespace',
                    '--cache', 'always',
                    '--allow-direct-io',
                    '--posix-acl',
                    '--xattr'
                ], close_fds=True
            ),
            call(
                [
                    '/usr/libexec/virtiofsd',
                    '--socket-path=/tmp/vhostqemu_1',
                    '--shared-dir', 'abspath/target',
                    '--sandbox', 'namespace',
                    '--cache', 'always',
                    '--allow-direct-io',
                    '--posix-acl',
                    '--xattr'
                ], close_fds=True
            ),
            call(
                [
                    '/usr/libexec/virtiofsd',
                    '--socket-path=/tmp/vhostqemu_2',
                    '--shared-dir', 'abspath/var/tmp/repos',
                    '--sandbox', 'namespace',
                    '--cache', 'always',
                    '--allow-direct-io',
                    '--posix-acl',
                    '--xattr'
                ], close_fds=True
            )
        ]
        for virtiofsd_process in defaults.VIRTIOFSD_PROCESS_LIST:
            virtiofsd_process.terminate.assert_called_once_with()

    @patch('pwd.getpwuid')
    @patch('time.sleep')
    @patch('os.path.isfile')
    @patch('os.system')
    @patch('kiwi.boxbuild.box_build.Command.run')
    @patch('kiwi.boxbuild.box_build.BoxBuildDefaults.create_build_target_dir')
    @patch('kiwi.boxbuild.defaults.Path.which')
    def test_run_with_sshfs_sharing(
        self, mock_path_which, mock_create_build_target_dir, mock_Command_run,
        mock_os_system, mock_os_path_isfile, mock_time_sleep,
        mock_pwd_getpwuid
    ):
        def command_run(args, raise_on_error=True):
            if args[0] == 'ssh':
                raise Exception

        def path_which(name, lookup=None):
            if name == 'qemu-system-x86_64':
                return 'qemu-system-x86_64'

        mock_path_which.side_effect = path_which
        mock_Command_run.side_effect = command_run

        mock_pwd_getpwuid.return_value.pw_name = 'user'
        mock_os_path_isfile.return_value = False
        self.build.sharing_backend = 'sshfs'
        self.build.ssh_port = '10022'

        with raises(KiwiBoxSSHKeyNotFound):
            self.build.run(
                [
                    '--type', 'oem', 'system', 'build',
                    '--description', 'desc', '--target-dir', 'target'
                ],
                keep_open=True,
                kiwi_version='9.22.1',
                custom_shared_path='var/tmp/repos'
            )

        mock_create_build_target_dir.reset_mock()
        mock_os_path_isfile.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            with patch.dict('os.environ', {'HOME': '~'}):
                file_handle = mock_open.return_value.__enter__.return_value
                file_handle.read.return_value = 'key_type key_value'
                self.build.run(
                    [
                        '--type', 'oem', 'system', 'build',
                        '--description', 'desc', '--target-dir', 'target'
                    ],
                    keep_open=True,
                    kiwi_version='9.22.1',
                    custom_shared_path='var/tmp/repos'
                )

        mock_create_build_target_dir.assert_called_once_with('target')
        mock_os_system.assert_called_once_with(
            'qemu-system-x86_64 '
            '-m 4096 '
            '-accel accel=kvm '
            '-cpu host '
            '-nographic '
            '-nodefaults '
            '-snapshot '
            '-kernel kernel '
            '-append "console=hvc0 kiwi=\\"--type oem system build\\"'
            ' kiwi-no-halt kiwi_version=_9.22.1_'
            ' custom_mount=_var/tmp/repos_'
            ' ssh_key=_key_value_'
            ' ssh_key_type=_key_type_'
            ' host_kiwidescription=_user@localhost:desc_'
            ' host_kiwibundle=_user@localhost:target_'
            ' host_custompath=_user@localhost:var/tmp/repos_'
            ' sharing_backend=_sshfs_" '
            '-drive file=system,if=virtio,driver=qcow2,cache=off,snapshot=on '
            '-nic user,model=virtio,hostfwd=tcp::10022-:22 '
            '-device virtio-serial '
            '-chardev stdio,id=virtiocon0 '
            '-device virtconsole,chardev=virtiocon0 '
            '-initrd initrd '
            '-smp 4'
        )
        assert mock_Command_run.call_args_list[0] == call(
            [
                'ssh-keygen', '-R', '[localhost]:10022'
            ], raise_on_error=False
        )
        assert mock_Command_run.call_args_list[1] == call(
            [
                'ssh', '-NT', '-o', 'StrictHostKeyChecking=no',
                'root@localhost', '-p', '10022', '-R',
                '10000:localhost:22'
            ]
        )
