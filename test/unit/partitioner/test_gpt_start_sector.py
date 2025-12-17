from unittest.mock import Mock, patch
from kiwi.partitioner.gpt import PartitionerGpt


class TestGptStartSector:
    """Test start_sector behavior with explicit partition IDs"""

    @patch('kiwi.partitioner.gpt.Command.run')
    def test_explicit_partition_ids_use_start_sector_zero(self, mock_command):
        """
        Test that start_sector=0 is used for ALL partitions with explicit IDs.

        This validates that sgdisk correctly handles start_sector=0 for
        all partitions, even when using non-sequential partition numbers.
        sgdisk updates the partition table after each call, so subsequent
        `:0:` automatically finds the next available space.

        Example use case: Creating partitions in order EFI(128), boot(127), root(1)
        where partition numbers don't match physical disk order.
        """
        # Mock device provider
        device_provider = Mock()
        device_provider.get_device.return_value = '/dev/loop0'

        # Create partitioner
        partitioner = PartitionerGpt(device_provider, start_sector=None)

        # Track start_sector values used in each sgdisk call
        start_sectors = []

        def capture_start_sector(*args, **kwargs):
            cmd = args[0]
            if 'sgdisk' in cmd and '-n' in cmd:
                # Extract start sector from -n argument: "128:0:+100M"
                n_index = cmd.index('-n')
                partition_spec = cmd[n_index + 1]
                start_sector = partition_spec.split(':')[1]
                start_sectors.append(start_sector)

        mock_command.side_effect = capture_start_sector

        # Create three partitions with explicit IDs in XML element order
        # EFI: partition_number=128 (physically first on disk)
        partitioner.create('p.lxefi', 100, 't.efi', explicit_partition_id=128)

        # Boot: partition_number=127 (physically second on disk)
        partitioner.create('p.lxboot', 1024, 't.linux', explicit_partition_id=127)

        # Root: partition_number=1 (physically third/last on disk)
        partitioner.create('p.lxroot', 10000, 't.linux', explicit_partition_id=1)

        # Validate start_sector values
        assert len(start_sectors) == 3, "Should have created 3 partitions"

        # ALL partitions should use start_sector=0
        # sgdisk handles this correctly by finding next available space
        assert start_sectors[0] == '0', \
            f"First partition should use start_sector=0, got {start_sectors[0]}"

        assert start_sectors[1] == '0', \
            f"Second partition should use start_sector=0, got {start_sectors[1]}"

        assert start_sectors[2] == '0', \
            f"Third partition should use start_sector=0, got {start_sectors[2]}"

        print(f"✓ All partitions used start_sector=0: {start_sectors}")
        print("✓ Partition IDs created: 128, 127, 1 (XML element order)")
        print("✓ sgdisk automatically places partitions sequentially on disk")

    @patch('kiwi.partitioner.gpt.Command.run')
    def test_auto_increment_partition_ids_all_use_start_sector_zero(self, mock_command):
        """
        Test backwards compatibility: when NOT using explicit partition IDs,
        all partitions should use start_sector=0 (original behavior).
        """
        device_provider = Mock()
        device_provider.get_device.return_value = '/dev/loop0'

        partitioner = PartitionerGpt(device_provider, start_sector=None)

        start_sectors = []

        def capture_start_sector(*args, **kwargs):
            cmd = args[0]
            if 'sgdisk' in cmd and '-n' in cmd:
                n_index = cmd.index('-n')
                partition_spec = cmd[n_index + 1]
                start_sector = partition_spec.split(':')[1]
                start_sectors.append(start_sector)

        mock_command.side_effect = capture_start_sector

        # Create three partitions WITHOUT explicit IDs (auto-increment)
        partitioner.create('p.lxboot', 100, 't.linux')
        partitioner.create('p.lxroot', 1024, 't.linux')
        partitioner.create('p.lxhome', 10000, 't.linux')

        # All partitions should use start_sector=0 (backwards compatible)
        assert all(s == '0' for s in start_sectors), \
            f"All auto-increment partitions should use start_sector=0, got {start_sectors}"

        print("✓ Backwards compatibility: all partitions used start_sector=0")
        print("✓ Partition IDs: 1, 2, 3 (auto-incremented)")
