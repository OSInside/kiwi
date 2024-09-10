from collections import namedtuple
from unittest.mock import (
    patch, Mock, MagicMock
)
from pytest import (
    raises, fixture
)
import kiwi

from kiwi.builder.enclave import EnclaveBuilder
from kiwi.exceptions import (
    KiwiEnclaveBootImageError,
    KiwiEnclaveFormatError
)


class TestEnclaveBuilder:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.builder.enclave.BootImage')
    def setup(self, mock_boot):
        self.setup = Mock()
        self.runtime_config = Mock()
        self.runtime_config.get_max_size_constraint = Mock(
            return_value=None
        )
        kiwi.builder.enclave.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )
        kiwi.builder.enclave.SystemSetup = Mock(
            return_value=self.setup
        )
        self.boot_image_task = MagicMock()
        self.boot_image_task.boot_root_directory = 'initrd_dir'
        self.boot_image_task.initrd_filename = 'initrd_file_name'
        mock_boot.new.return_value = self.boot_image_task
        self.xml_state = Mock()
        self.xml_state.profiles = None
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        self.xml_state.get_initrd_system = Mock(
            return_value='dracut'
        )
        self.xml_state.xml_data.get_name = Mock(
            return_value='some-image'
        )
        self.xml_state.build_type = Mock()
        self.xml_state.build_type.get_kernelcmdline = Mock(
            return_value='some'
        )
        kernel_type = namedtuple(
            'kernel', ['filename', 'version']
        )
        self.kernel = Mock()
        self.kernel.get_kernel = Mock(
            return_value=kernel_type(filename='some-kernel', version='42')
        )
        kiwi.builder.enclave.Kernel = Mock(
            return_value=self.kernel
        )
        self.enclave = EnclaveBuilder(
            self.xml_state, 'target_dir', 'root_dir',
            custom_args={'signing_keys': ['key_file_a', 'key_file_b']}
        )
        self.enclave.compressed = True

    @patch('kiwi.builder.enclave.BootImage')
    def setup_method(self, cls, mock_boot):
        self.setup()

    @patch('kiwi.builder.enclave.BootImage')
    def test_create_invalid_enclave_format(self, mock_boot):
        self.enclave.format = ''
        with raises(KiwiEnclaveFormatError):
            self.enclave.create()

    @patch('kiwi.builder.enclave.Command.run')
    def test_create_aws_nitro(self, mock_Command_run):
        self.enclave.format = 'aws-nitro'
        self.boot_image_task.required = Mock(
            return_value=True
        )
        self.enclave.create()

        self.boot_image_task.create_initrd.assert_called_once_with()
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        mock_Command_run.assert_called_once_with(
            [
                'eif_build',
                '--kernel', 'target_dir/some-image.x86_64-1.2.3-42.kernel',
                '--ramdisk', 'target_dir/initrd_file_name',
                '--cmdline', 'some',
                '--output', 'target_dir/some-image.x86_64-1.2.3.eif'
            ]
        )

    def test_create_no_kernel_found(self):
        self.kernel.get_kernel.return_value = False
        with raises(KiwiEnclaveBootImageError):
            self.enclave.create()
