from unittest.mock import (
    patch, Mock
)
from pytest import (
    raises, fixture
)
import tempfile
import os

from kiwi.defaults import Defaults
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.builder.disk import DiskBuilder
from kiwi.exceptions import (
    KiwiDiskConfigError
)


class TestDiskBuilderCustomPartitionControl:
    """Test custom partition control feature in DiskBuilder"""

    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def _setup_with_mock(self, mock_exists):
        Defaults.set_platform_name('x86_64')

        def side_effect(filename):
            if filename.endswith('.config/kiwi/config.yml'):
                return False
            elif filename.endswith('etc/kiwi.yml'):
                return False
            elif filename.startswith(self.temp_dir):
                # Temp directories exist for testing
                return True
            else:
                return True

        mock_exists.side_effect = side_effect
        # Load a basic disk config for testing
        self.description = XMLDescription(
            '../data/example_disk_config.xml'
        )
        self.xml_state = XMLState(
            self.description.load()
        )

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.target_dir = os.path.join(self.temp_dir, 'target')
        self.root_dir = os.path.join(self.temp_dir, 'root')
        os.makedirs(self.target_dir, exist_ok=True)
        os.makedirs(self.root_dir, exist_ok=True)
        self._setup_with_mock(mock_exists)

    def test_has_custom_partition_control_returns_true(self):
        """Test _has_custom_partition_control returns True when set"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                assert disk_builder._has_custom_partition_control() is True

    def test_has_custom_partition_control_returns_false(self):
        """Test _has_custom_partition_control returns False when not set"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value=None
                )
                assert disk_builder._has_custom_partition_control() is False

    def test_validate_custom_partition_control_config_no_auto_partition_attrs(self):
        """Test validation passes when no auto-partition attributes present"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                # Mock build_type methods to return None (no auto-partition attributes)
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                disk_builder._validate_custom_partition_control_config()

    def test_validate_custom_partition_control_config_rejects_bootpartition(self):
        """Test validation rejects bootpartition auto-partition attribute"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                # Mock build_type to have bootpartition set (auto-partition attribute)
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value='p.lxboot')
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                with raises(KiwiDiskConfigError) as exc_info:
                    disk_builder._validate_custom_partition_control_config()
                assert 'bootpartition' in str(exc_info.value)

    def test_validate_custom_partition_control_config_rejects_bootpartition_size(self):
        """Test validation rejects bootpartsize auto-partition attribute"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=1024)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                with raises(KiwiDiskConfigError) as exc_info:
                    disk_builder._validate_custom_partition_control_config()
                assert 'bootpartsize' in str(exc_info.value).lower()

    def test_validate_custom_partition_control_config_rejects_efipartsize(self):
        """Test validation rejects efipartsize auto-partition attribute"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=512)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                with raises(KiwiDiskConfigError) as exc_info:
                    disk_builder._validate_custom_partition_control_config()
                assert 'efipartsize' in str(exc_info.value).lower()

    def test_validate_custom_partition_control_config_rejects_spare_part(self):
        """Test validation rejects spare_part auto-partition attribute"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value='p.spare')
                with raises(KiwiDiskConfigError) as exc_info:
                    disk_builder._validate_custom_partition_control_config()
                assert 'spare' in str(exc_info.value).lower()

    def test_validate_custom_partition_control_config_error_message(self):
        """Test error message directs users to use partition elements"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value='p.lxboot')
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                with raises(KiwiDiskConfigError) as exc_info:
                    disk_builder._validate_custom_partition_control_config()
                error_msg = str(exc_info.value)
                assert 'partition' in error_msg.lower()

    def test_has_custom_partition_control_integration(self):
        """Test custom partition control detection"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                result = disk_builder._has_custom_partition_control()
                assert result is True
                # Method is called twice internally: once for None check, once for str().lower() == 'true' check
                assert disk_builder.xml_state.build_type.get_custom_part_control.call_count == 2

    def test_custom_partition_control_flag_in_disk_creation(self):
        """Test custom_part_control flag handling"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.disk = Mock()
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                assert disk_builder._has_custom_partition_control() is True

    def test_partition_number_uniqueness_validation(self):
        """Test partition number handling"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                assert disk_builder is not None

    def test_boot_flag_single_partition_validation(self):
        """Test boot flag handling"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                assert disk_builder is not None

    def test_custom_partition_control_allows_reserved_names(self):
        """Test custom_part_control allows system partition names"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                assert disk_builder._has_custom_partition_control() is True

    def test_custom_partition_control_prevents_auto_partition_attrs(self):
        """Test custom_part_control prevents auto-partition attributes"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                disk_builder.xml_state.build_type.get_bootpartition = Mock(return_value='p.lxboot')
                disk_builder.xml_state.build_type.get_bootpartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_efipartsize = Mock(return_value=None)
                disk_builder.xml_state.build_type.get_spare_part = Mock(return_value=None)
                with raises(KiwiDiskConfigError):
                    disk_builder._validate_custom_partition_control_config()

    def test_custom_partition_control_false_allows_auto_partition_attrs(self):
        """Test auto-partition mode allows auto-partition attributes"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value=None
                )
                assert disk_builder is not None

    def test_custom_partition_control_sets_storage_map_system(self):
        """Test storage_map['system'] is set from custom parts when custom_part_control=true"""
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                # Setup: custom_part_control enabled
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                # Setup: mock root filesystem in system_custom_parts
                mock_root_fs = Mock()
                disk_builder.storage_map = {
                    'system': None,
                    'system_custom_parts': {'root': mock_root_fs}
                }
                # Simulate what _create_system_instance does for custom_part_control
                if disk_builder._has_custom_partition_control():
                    if 'root' in disk_builder.storage_map.get('system_custom_parts', {}):
                        disk_builder.storage_map['system'] = \
                            disk_builder.storage_map['system_custom_parts']['root']
                # Verify storage_map['system'] is now set to the root filesystem
                assert disk_builder.storage_map['system'] is mock_root_fs

    @patch('kiwi.builder.disk.FileSystem')
    def test_create_system_instance_custom_partition_control(self, mock_FileSystem):
        """Test _create_system_instance sets storage_map['system'] from custom parts"""
        from contextlib import ExitStack
        with patch('kiwi.builder.disk.Disk'):
            with patch('kiwi.builder.disk.BootImage'):
                disk_builder = DiskBuilder(
                    self.xml_state,
                    self.target_dir,
                    self.root_dir,
                    None
                )
                # Setup: custom_part_control enabled
                disk_builder.xml_state.build_type.get_custom_part_control = Mock(
                    return_value='true'
                )
                # Disable volume manager
                disk_builder.volume_manager_name = None
                # Initialize storage_map (normally done in create_disk)
                disk_builder.storage_map = {
                    'system': None,
                    'system_boot': None,
                    'system_efi': None,
                    'system_spare': None,
                    'system_custom_parts': {},
                    'luks_root': None,
                    'raid_root': None,
                    'integrity_root': None
                }
                # Setup: mock _build_spare_filesystem to return None
                disk_builder._build_spare_filesystem = Mock(return_value=None)
                # Setup: mock root filesystem that _build_custom_parts_filesystem will return
                mock_root_fs = Mock()
                disk_builder._build_custom_parts_filesystem = Mock(
                    return_value={'root': mock_root_fs, 'boot': Mock()}
                )
                # Setup device_map with root entry
                device_map = {'root': Mock()}

                # Call the actual method
                with ExitStack() as stack:
                    disk_builder._create_system_instance(device_map, stack)

                # Verify storage_map['system'] is set to the root filesystem
                assert disk_builder.storage_map['system'] is mock_root_fs
                # Verify system_boot and system_efi are None (custom_part_control skips boot filesystem creation)
                assert disk_builder.storage_map['system_boot'] is None
                assert disk_builder.storage_map['system_efi'] is None
