import logging
from unittest.mock import patch, call

from kiwi.system.summary import ImageSummary
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState


class TestImageSummary:
    def setup(self):
        self.xml_data = XMLDescription('../data/example_config.xml').load()

    def setup_method(self, cls):
        self.setup()

    def _summary(self, profiles, build_type=None):
        return ImageSummary(
            XMLState(self.xml_data, profiles, build_type),
            'config.xml',
            'x86_64',
        )

    @patch('kiwi.firmware.Defaults.get_platform_name')
    def test_disk(self, mock_get_platform_name):
        mock_get_platform_name.return_value = 'x86_64'
        summary = self._summary(['vmxFlavour'], 'oem')
        assert summary.get_information() == [
            ('Image', 'LimeJeOS 1.13.2'),
            ('Description', 'config.xml'),
            ('Type', 'oem (x86_64)'),
            ('Profiles', 'vmxFlavour'),
            ('Filesystem', 'btrfs'),
            ('Firmware', 'efi'),
            ('Bootloader', 'grub2'),
            ('Package manager', 'zypper'),
        ]
        # a repository without a type uses the package manager default
        assert summary.get_repositories() == [
            'iso:///image/CDs/dvd.iso',
            'rpm-md obs://Devel:PubCloud:AmazonEC2/SLE_12_GA',
        ]
        assert summary.get_features() == [
            ('Secure boot', False),
            ('Legacy BIOS boot', True),
            ('LUKS encryption', True),
            ('LVM', False),
            ('Btrfs snapshots', True),
            ('Software RAID', False),
            ('Overlay root', False),
            ('dm-verity', False),
            ('dm-integrity', False),
            ('Swap partition', True),
            ('Resize on first boot', True),
            ('Install ISO', True),
            ('Install PXE', False),
            ('Package signature check', True),
            ('Documentation excluded', True),
        ]

    @patch('kiwi.firmware.Defaults.get_platform_name')
    def test_live(self, mock_get_platform_name):
        mock_get_platform_name.return_value = 'x86_64'
        summary = self._summary(['vmxSimpleFlavour'], 'iso')
        assert ('Format', 'vmdk') not in summary.get_information()
        assert summary.get_features() == [
            ('Secure boot', False),
            ('Legacy BIOS boot', True),
            ('LUKS encryption', False),
            ('Persistent storage', False),
            ('Media check', True),
            ('Package signature check', True),
            ('Documentation excluded', True),
        ]

    def test_container(self):
        summary = self._summary(['derivedContainer'])
        assert summary.get_information() == [
            ('Image', 'LimeJeOS 1.13.2'),
            ('Description', 'config.xml'),
            ('Type', 'docker (x86_64)'),
            ('Profiles', 'derivedContainer'),
            ('Base image', 'obs://project/repo/image#mytag'),
            ('Package manager', 'zypper'),
        ]
        assert summary.get_features() == [
            ('Package signature check', True),
            ('Documentation excluded', True),
        ]

    def test_format(self):
        summary = self._summary(['vmxSimpleFlavour'], 'oem')
        assert ('Format', 'vmdk') in summary.get_information()

    @patch('kiwi.system.summary.log')
    def test_print_summary(self, mock_log):
        summary = self._summary(['derivedContainer'])
        summary.print_summary()
        mock_log.phase.assert_called_once_with('Image summary')
        assert mock_log.item.call_args_list[-4:] == [
            call('Repositories', 'iso:///image/CDs/dvd.iso'),
            call(
                'Repositories',
                'rpm-md obs://Devel:PubCloud:AmazonEC2/SLE_12_GA',
            ),
            call('Features', 'Package signature check', checked=True),
            call('Features', 'Documentation excluded', checked=True),
        ]

    @patch('kiwi.defaults.Defaults.get_platform_name')
    def test_default_arch(self, mock_get_platform_name):
        mock_get_platform_name.return_value = 'aarch64'
        logging.disable(logging.CRITICAL)
        summary = ImageSummary(
            XMLState(self.xml_data, ['derivedContainer']), 'config.xml'
        )
        logging.disable(logging.NOTSET)
        assert summary.arch == 'aarch64'
