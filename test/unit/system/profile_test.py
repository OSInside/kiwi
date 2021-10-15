# vim: set fileencoding=utf-8
from mock import patch

import os

from kiwi.system.profile import Profile
from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription


class TestProfile:
    def setup(self):
        self.profile_file = 'tmpfile.profile'
        description = XMLDescription('../data/example_dot_profile_config.xml')
        self.profile = Profile(
            XMLState(description.load())
        )

    @patch('kiwi.path.Path.which')
    def test_create(self, mock_which):
        mock_which.return_value = 'cp'
        self.profile.create(self.profile_file)
        os.remove(self.profile_file)
        assert self.profile.dot_profile == {
            'kiwi_Volume_1': 'usr_lib|size:1024|usr/lib',
            'kiwi_Volume_2': 'etc_volume|freespace:30|etc',
            'kiwi_Volume_3': 'bin_volume|size:all|/usr/bin',
            'kiwi_Volume_4': 'usr_bin|freespace:30|usr/bin',
            'kiwi_Volume_5': 'LVSwap|size:128|',
            'kiwi_Volume_Root': 'LVRoot|freespace:500|',
            'kiwi_bootkernel': None,
            'kiwi_bootloader': 'grub2',
            'kiwi_bootprofile': None,
            'kiwi_target_removable': None,
            'kiwi_boot_timeout': None,
            'kiwi_cmdline': 'splash',
            'kiwi_compressed': None,
            'kiwi_delete': '',
            'kiwi_devicepersistency': None,
            'kiwi_bootloader_console': None,
            'kiwi_displayname': 'schäfer',
            'kiwi_drivers': '',
            'kiwi_firmware': 'efi',
            'kiwi_fsmountoptions': None,
            'kiwi_hybridpersistent_filesystem': None,
            'kiwi_hybridpersistent': None,
            'kiwi_iname': 'LimeJeOS-openSUSE-13.2',
            'kiwi_installboot': None,
            'kiwi_iversion': '1.13.2',
            'kiwi_keytable': 'us.map.gz',
            'kiwi_language': 'en_US',
            'kiwi_loader_theme': 'openSUSE',
            'kiwi_lvm': 'true',
            'kiwi_lvmgroup': 'systemVG',
            'kiwi_oembootwait': None,
            'kiwi_oemdevicefilter': None,
            'kiwi_oemnicfilter': None,
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
            'kiwi_oemresizeonce': None,
            'kiwi_oemshutdown': None,
            'kiwi_oemsilentboot': None,
            'kiwi_oemsilentinstall': None,
            'kiwi_oemsilentverify': None,
            'kiwi_oemskipverify': 'true',
            'kiwi_oemswapMB': None,
            'kiwi_oemtitle': 'schäfer',
            'kiwi_oemunattended_id': None,
            'kiwi_oemunattended': None,
            'kiwi_oemvmcp_parmfile': None,
            'kiwi_profiles': '',
            'kiwi_ramonly': True,
            'kiwi_initrd_system': 'dracut',
            'kiwi_install_volid': 'INSTALL',
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
            'kiwi_startsector': 2048,
            'kiwi_luks_empty_passphrase': True,
            'kiwi_wwid_wait_timeout': None,
            'kiwi_xendomain': 'dom0',
            'kiwi_rootpartuuid': None
        }

    @patch('kiwi.path.Path.which')
    def test_create_displayname_is_image_name(self, mock_which):
        mock_which.return_value = 'cp'
        description = XMLDescription('../data/example_pxe_config.xml')
        profile = Profile(
            XMLState(description.load())
        )
        profile.create(self.profile_file)
        os.remove(self.profile_file)
        assert profile.dot_profile['kiwi_displayname'] == \
            'LimeJeOS-openSUSE-13.2'

    @patch('kiwi.path.Path.which')
    def test_create_cpio(self, mock_which):
        mock_which.return_value = 'cp'
        description = XMLDescription('../data/example_dot_profile_config.xml')
        profile = Profile(
            XMLState(description.load(), None, 'cpio')
        )
        profile.create(self.profile_file)
        os.remove(self.profile_file)
        assert profile.dot_profile['kiwi_cpio_name'] == \
            'LimeJeOS-openSUSE-13.2'

    def test_add(self):
        self.profile.add('foo', 'bar')
        assert self.profile.dot_profile['foo'] == 'bar'

    def test_delete(self):
        self.profile.add('foo', 'bar')
        self.profile.delete('foo')
        assert 'foo' not in self.profile.dot_profile
