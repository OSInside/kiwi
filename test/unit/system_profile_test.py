
from mock import patch

import mock
import os

from .test_helper import *

from kiwi.exceptions import (
    KiwiUriStyleUnknown,
    KiwiUriTypeUnknown
)

from kiwi.system.profile import Profile
from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription


class TestProfile(object):
    def setup(self):
        self.tmpfile = mock.Mock()
        self.tmpfile.name = 'tmpfile'
        description = XMLDescription('../data/example_dot_profile_config.xml')
        self.profile = Profile(
            XMLState(description.load())
        )

    @patch('kiwi.system.profile.NamedTemporaryFile')
    def test_create(self, mock_temp):
        mock_temp.return_value = self.tmpfile
        result = self.profile.create()
        os.remove(self.tmpfile.name)
        print(self.profile.dot_profile)
        assert self.profile.dot_profile == {
            'kiwi_allFreeVolume_bin_volume': 'size:all:LVusr_bin',
            'kiwi_allFreeVolume_LVusr_bin': 'size:all',
            'kiwi_bootkernel': None,
            'kiwi_bootloader': 'grub2',
            'kiwi_bootprofile': None,
            'kiwi_boot_timeout': None,
            'kiwi_cmdline': 'splash',
            'kiwi_compressed': None,
            'kiwi_delete': '',
            'kiwi_devicepersistency': None,
            'kiwi_displayname': 'LimeJeOS-openSUSE-13.2',
            'kiwi_drivers': '',
            'kiwi_firmware': 'efi',
            'kiwi_fsmountoptions': None,
            'kiwi_hwclock': 'utc',
            'kiwi_hybrid': True,
            'kiwi_hybridpersistent_filesystem': None,
            'kiwi_hybridpersistent': None,
            'kiwi_iname': 'LimeJeOS-openSUSE-13.2',
            'kiwi_installboot': None,
            'kiwi_iversion': '1.13.2',
            'kiwi_keytable': 'us.map.gz',
            'kiwi_language': 'en_US',
            'kiwi_loader_theme': 'openSUSE',
            'kiwi_LVM_etc_volume': 'freespace:30:LVetc',
            'kiwi_LVM_LVRoot': 'freespace:500',
            'kiwi_LVM_LVusr_lib': 'size:1024',
            'kiwi_lvm': 'true',
            'kiwi_lvmgroup': 'systemVG',
            'kiwi_oemataraid_scan': None,
            'kiwi_oembootwait': None,
            'kiwi_oemdevicefilter': None,
            'kiwi_oemkboot': None,
            'kiwi_oemmultipath_scan': None,
            'kiwi_oempartition_install': None,
            'kiwi_oemrebootinteractive': None,
            'kiwi_oemreboot': None,
            'kiwi_oemrecoveryID': None,
            'kiwi_oemrecoveryInPlace': None,
            'kiwi_oemrecovery': False,
            'kiwi_oemrecoveryPartSize': None,
            'kiwi_oemrootMB': 2048,
            'kiwi_oemshutdowninteractive': None,
            'kiwi_oemshutdown': None,
            'kiwi_oemsilentboot': None,
            'kiwi_oemsilentinstall': None,
            'kiwi_oemsilentverify': None,
            'kiwi_oemskipverify': None,
            'kiwi_oemswapMB': None,
            'kiwi_oemswap': 'true',
            'kiwi_oemtitle': None,
            'kiwi_oemunattended_id': None,
            'kiwi_oemunattended': None,
            'kiwi_oemvmcp_parmfile': None,
            'kiwi_profiles': '',
            'kiwi_ramonly': None,
            'kiwi_initrd_system': None,
            'kiwi_btrfs_root_is_snapshot': None,
            'kiwi_gpt_hybrid_mbr': None,
            'kiwi_showlicense': None,
            'kiwi_splash_theme': 'openSUSE',
            'kiwi_strip_delete': '',
            'kiwi_strip_libs': '',
            'kiwi_strip_tools': '',
            'kiwi_target_blocksize': None,
            'kiwi_timezone': 'Europe/Berlin',
            'kiwi_type': 'oem',
            'kiwi_vga': None,
            'kiwi_wwid_wait_timeout': None,
            'kiwi_xendomain': None
        }
        assert result == [
            "kiwi_LVM_LVRoot='freespace:500'",
            "kiwi_LVM_LVusr_lib='size:1024'",
            "kiwi_LVM_etc_volume='freespace:30:LVetc'",
            "kiwi_allFreeVolume_LVusr_bin='size:all'",
            "kiwi_allFreeVolume_bin_volume='size:all:LVusr_bin'",
            "kiwi_bootloader='grub2'",
            "kiwi_cmdline='splash'",
            "kiwi_displayname='LimeJeOS-openSUSE-13.2'",
            "kiwi_firmware='efi'",
            "kiwi_hwclock='utc'",
            "kiwi_hybrid='true'",
            "kiwi_iname='LimeJeOS-openSUSE-13.2'",
            "kiwi_iversion='1.13.2'",
            "kiwi_keytable='us.map.gz'",
            "kiwi_language='en_US'",
            "kiwi_loader_theme='openSUSE'",
            "kiwi_lvm='true'",
            "kiwi_lvmgroup='systemVG'",
            "kiwi_oemrootMB='2048'",
            "kiwi_oemswap='true'",
            "kiwi_splash_theme='openSUSE'",
            "kiwi_timezone='Europe/Berlin'",
            "kiwi_type='oem'"
        ]

    @patch('kiwi.system.profile.NamedTemporaryFile')
    def test_create_cpio(self, mock_temp):
        mock_temp.return_value = self.tmpfile
        description = XMLDescription('../data/example_dot_profile_config.xml')
        profile = Profile(
            XMLState(description.load(), None, 'cpio')
        )
        profile.create()
        os.remove(self.tmpfile.name)
        assert profile.dot_profile['kiwi_cpio_name'] == 'LimeJeOS-openSUSE-13.2'

    def test_add(self):
        self.profile.add('foo', 'bar')
        assert self.profile.dot_profile['foo'] == 'bar'
