import logging
from collections import namedtuple
from mock import (
    patch, Mock
)
from pytest import (
    raises, fixture
)

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription

from kiwi.exceptions import (
    KiwiTypeNotFound,
    KiwiDistributionNameError,
    KiwiProfileNotFound
)


class TestXMLState:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        self.description = XMLDescription(
            '../data/example_config.xml'
        )
        self.state = XMLState(
            self.description.load()
        )
        boot_description = XMLDescription(
            '../data/isoboot/example-distribution/config.xml'
        )
        self.boot_state = XMLState(
            boot_description.load()
        )
        no_image_packages_description = XMLDescription(
            '../data/example_no_image_packages_config.xml'
        )
        self.no_image_packages_boot_state = XMLState(
            no_image_packages_description.load()
        )
        self.bootloader = Mock()
        self.bootloader.get_name.return_value = 'some-loader'
        self.bootloader.get_timeout.return_value = 'some-timeout'
        self.bootloader.get_timeout_style.return_value = 'some-style'
        self.bootloader.get_targettype.return_value = 'some-target'
        self.bootloader.get_console.return_value = 'some-console'
        self.bootloader.get_serial_line.return_value = 'some-serial'

    def test_get_description_section(self):
        description = self.state.get_description_section()
        assert description.author == 'Marcus'
        assert description.contact == 'ms@suse.com'
        assert description.specification == \
            'Testing various configuration states'

    @patch('platform.machine')
    def test_get_preferences_by_architecture(self, mock_machine):
        mock_machine.return_value = 'aarch64'
        state = XMLState(
            self.description.load()
        )
        preferences = state.get_preferences_sections()
        assert len(preferences) == 3
        assert preferences[2].get_arch() == 'aarch64'
        assert state.get_build_type_name() == 'iso'

    def test_build_type_primary_selected(self):
        assert self.state.get_build_type_name() == 'oem'

    def test_build_type_first_selected(self):
        self.state.xml_data.get_preferences()[2].get_type()[0].set_primary(
            False
        )
        assert self.state.get_build_type_name() == 'oem'

    @patch('kiwi.xml_state.XMLState.get_preferences_sections')
    def test_get_rpm_excludedocs_without_entry(self, mock_preferences):
        mock_preferences.return_value = []
        assert self.state.get_rpm_excludedocs() is False

    def test_get_rpm_excludedocs(self):
        assert self.state.get_rpm_excludedocs() is True

    @patch('kiwi.xml_state.XMLState.get_preferences_sections')
    def test_get_rpm_check_signatures_without_entry(self, mock_preferences):
        mock_preferences.return_value = []
        assert self.state.get_rpm_check_signatures() is False

    def test_get_rpm_check_signatures(self):
        assert self.state.get_rpm_check_signatures() is True

    def test_get_package_manager(self):
        assert self.state.get_package_manager() == 'zypper'

    @patch('kiwi.xml_state.XMLState.get_preferences_sections')
    def test_get_default_package_manager(self, mock_preferences):
        mock_preferences.return_value = []
        assert self.state.get_package_manager() == 'dnf'

    def test_get_image_version(self):
        assert self.state.get_image_version() == '1.13.2'

    def test_get_bootstrap_packages(self):
        assert self.state.get_bootstrap_packages() == [
            'filesystem', 'zypper'
        ]
        assert self.state.get_bootstrap_packages(plus_packages=['vim']) == [
            'filesystem', 'vim', 'zypper'
        ]
        assert self.no_image_packages_boot_state.get_bootstrap_packages() == [
            'patterns-openSUSE-base'
        ]

    def test_get_system_packages(self):
        assert self.state.get_system_packages() == [
            'gfxboot-branding-openSUSE',
            'grub2-branding-openSUSE',
            'ifplugd',
            'iputils',
            'kernel-default',
            'openssh',
            'plymouth-branding-openSUSE',
            'vim'
        ]

    @patch('platform.machine')
    def test_get_system_packages_some_arch(self, mock_machine):
        mock_machine.return_value = 's390'
        state = XMLState(
            self.description.load()
        )
        assert state.get_system_packages() == [
            'foo',
            'gfxboot-branding-openSUSE',
            'grub2-branding-openSUSE',
            'ifplugd',
            'iputils',
            'kernel-default',
            'openssh',
            'plymouth-branding-openSUSE',
            'vim'
        ]

    def test_get_system_collections(self):
        assert self.state.get_system_collections() == [
            'base'
        ]

    def test_get_system_products(self):
        assert self.state.get_system_products() == [
            'openSUSE'
        ]

    def test_get_system_archives(self):
        assert self.state.get_system_archives() == [
            '/absolute/path/to/image.tgz'
        ]

    def test_get_system_ignore_packages(self):
        assert self.state.get_system_ignore_packages() == [
            'bar', 'baz', 'foo'
        ]
        self.state.host_architecture = 'aarch64'
        assert self.state.get_system_ignore_packages() == [
            'baz', 'foo'
        ]
        self.state.host_architecture = 's390'
        assert self.state.get_system_ignore_packages() == [
            'baz'
        ]

    def test_get_system_collection_type(self):
        assert self.state.get_system_collection_type() == 'plusRecommended'

    def test_get_bootstrap_collections(self):
        assert self.state.get_bootstrap_collections() == [
            'bootstrap-collection'
        ]

    def test_get_bootstrap_products(self):
        assert self.state.get_bootstrap_products() == ['kiwi']

    def test_get_bootstrap_archives(self):
        assert self.state.get_bootstrap_archives() == ['bootstrap.tgz']

    def test_get_bootstrap_collection_type(self):
        assert self.state.get_bootstrap_collection_type() == 'onlyRequired'

    def test_set_repository(self):
        self.state.set_repository('repo', 'type', 'alias', 1, True, False)
        assert self.state.xml_data.get_repository()[0].get_source().get_path() \
            == 'repo'
        assert self.state.xml_data.get_repository()[0].get_type() == 'type'
        assert self.state.xml_data.get_repository()[0].get_alias() == 'alias'
        assert self.state.xml_data.get_repository()[0].get_priority() == 1
        assert self.state.xml_data.get_repository()[0] \
            .get_imageinclude() is True
        assert self.state.xml_data.get_repository()[0] \
            .get_package_gpgcheck() is False

    def test_add_repository(self):
        self.state.add_repository('repo', 'type', 'alias', 1, True)
        assert self.state.xml_data.get_repository()[3].get_source().get_path() \
            == 'repo'
        assert self.state.xml_data.get_repository()[3].get_type() == 'type'
        assert self.state.xml_data.get_repository()[3].get_alias() == 'alias'
        assert self.state.xml_data.get_repository()[3].get_priority() == 1
        assert self.state.xml_data.get_repository()[3] \
            .get_imageinclude() is True

    def test_add_repository_with_empty_values(self):
        self.state.add_repository('repo', 'type', '', '', True)
        assert self.state.xml_data.get_repository()[3].get_source().get_path() \
            == 'repo'
        assert self.state.xml_data.get_repository()[3].get_type() == 'type'
        assert self.state.xml_data.get_repository()[3].get_alias() == ''
        assert self.state.xml_data.get_repository()[3].get_priority() is None
        assert self.state.xml_data.get_repository()[3] \
            .get_imageinclude() is True

    def test_get_to_become_deleted_packages(self):
        assert self.state.get_to_become_deleted_packages() == [
            'kernel-debug'
        ]

    def test_get_build_type_vagrant_config_section(self):
        vagrant_config = self.state.get_build_type_vagrant_config_section()
        assert vagrant_config.get_provider() == 'libvirt'
        assert self.boot_state.get_build_type_vagrant_config_section() is None

    def test_virtualbox_guest_additions_vagrant_config_section(self):
        assert not self.state.get_vagrant_config_virtualbox_guest_additions()

    def test_virtualbox_guest_additions_vagrant_config_section_missing(self):
        self.state. \
            get_build_type_vagrant_config_section() \
            .virtualbox_guest_additions_present = True
        assert self.state.get_vagrant_config_virtualbox_guest_additions()

    def test_get_build_type_system_disk_section(self):
        assert self.state.get_build_type_system_disk_section().get_name() == \
            'mydisk'

    def test_get_build_type_vmdisk_section(self):
        assert self.state.get_build_type_vmdisk_section().get_id() == 0
        assert self.boot_state.get_build_type_vmdisk_section() is None

    def test_get_build_type_vmnic_entries(self):
        assert self.state.get_build_type_vmnic_entries()[0].get_interface() \
            == ''
        assert self.boot_state.get_build_type_vmnic_entries() == []

    def test_get_build_type_vmdvd_section(self):
        assert self.state.get_build_type_vmdvd_section().get_id() == 0
        assert self.boot_state.get_build_type_vmdvd_section() is None

    def test_get_volume_management(self):
        assert self.state.get_volume_management() == 'lvm'

    def test_get_volume_management_none(self):
        assert self.boot_state.get_volume_management() is None

    def test_get_volume_management_btrfs(self):
        description = XMLDescription('../data/example_btrfs_config.xml')
        xml_data = description.load()
        state = XMLState(xml_data)
        assert state.get_volume_management() == 'btrfs'

    def test_get_volume_management_lvm_prefer(self):
        description = XMLDescription('../data/example_lvm_preferred_config.xml')
        xml_data = description.load()
        state = XMLState(xml_data)
        assert state.get_volume_management() == 'lvm'

    def test_get_volume_management_lvm_default(self):
        description = XMLDescription('../data/example_lvm_default_config.xml')
        xml_data = description.load()
        state = XMLState(xml_data)
        assert state.get_volume_management() == 'lvm'

    def test_build_type_explicitly_selected(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'oem')
        assert state.get_build_type_name() == 'oem'

    def test_build_type_not_found(self):
        xml_data = self.description.load()
        with raises(KiwiTypeNotFound):
            XMLState(xml_data, ['vmxFlavour'], 'foo')

    def test_build_type_not_found_no_default_type(self):
        description = XMLDescription('../data/example_no_default_type.xml')
        xml_data = description.load()
        with raises(KiwiTypeNotFound):
            XMLState(xml_data, ['minimal'])

    def test_profile_not_found(self):
        xml_data = self.description.load()
        with raises(KiwiProfileNotFound):
            XMLState(xml_data, ['foo'])

    def test_profile_requires(self):
        xml_data = self.description.load()
        xml_state = XMLState(xml_data, ['composedProfile'])
        assert xml_state.profiles == [
            'composedProfile', 'vmxSimpleFlavour', 'xenDomUFlavour'
        ]

    def test_get_volumes_custom_root_volume_name(self):
        description = XMLDescription(
            '../data/example_lvm_custom_rootvol_config.xml'
        )
        xml_data = description.load()
        state = XMLState(xml_data)
        volume_type = namedtuple(
            'volume_type', [
                'name',
                'size',
                'realpath',
                'mountpoint',
                'fullsize',
                'label',
                'attributes',
                'is_root_volume'
            ]
        )
        assert state.get_volumes() == [
            volume_type(
                name='myroot', size='freespace:500',
                realpath='/',
                mountpoint=None, fullsize=False,
                label=None,
                attributes=[],
                is_root_volume=True
            )
        ]

    def test_get_volumes(self):
        description = XMLDescription('../data/example_lvm_default_config.xml')
        xml_data = description.load()
        state = XMLState(xml_data)
        volume_type = namedtuple(
            'volume_type', [
                'name',
                'size',
                'realpath',
                'mountpoint',
                'fullsize',
                'label',
                'attributes',
                'is_root_volume'
            ]
        )
        assert state.get_volumes() == [
            volume_type(
                name='usr_lib', size='size:1024',
                realpath='usr/lib',
                mountpoint='usr/lib',
                fullsize=False,
                label='library',
                attributes=[],
                is_root_volume=False
            ),
            volume_type(
                name='LVRoot', size='freespace:500',
                realpath='/',
                mountpoint=None, fullsize=False,
                label=None,
                attributes=[],
                is_root_volume=True
            ),
            volume_type(
                name='etc_volume', size='freespace:30',
                realpath='etc',
                mountpoint='etc', fullsize=False,
                label=None,
                attributes=['no-copy-on-write'],
                is_root_volume=False
            ),
            volume_type(
                name='bin_volume', size=None,
                realpath='/usr/bin',
                mountpoint='/usr/bin', fullsize=True,
                label=None,
                attributes=[],
                is_root_volume=False
            ),
            volume_type(
                name='LVSwap', size='size:128',
                realpath='swap',
                mountpoint=None, fullsize=False,
                label='SWAP',
                attributes=[],
                is_root_volume=False
            )
        ]

    def test_get_volumes_no_explicit_root_setup(self):
        description = XMLDescription('../data/example_lvm_no_root_config.xml')
        xml_data = description.load()
        state = XMLState(xml_data)
        volume_type = namedtuple(
            'volume_type', [
                'name',
                'size',
                'realpath',
                'mountpoint',
                'fullsize',
                'label',
                'attributes',
                'is_root_volume'
            ]
        )
        assert state.get_volumes() == [
            volume_type(
                name='LVRoot', size=None, realpath='/',
                mountpoint=None, fullsize=True,
                label=None,
                attributes=[],
                is_root_volume=True
            ),
            volume_type(
                name='LVSwap', size='size:128',
                realpath='swap',
                mountpoint=None, fullsize=False,
                label='SWAP',
                attributes=[],
                is_root_volume=False
            )
        ]

    def test_get_volumes_no_explicit_root_setup_other_fullsize_volume(self):
        description = XMLDescription(
            '../data/example_lvm_no_root_full_usr_config.xml'
        )
        xml_data = description.load()
        state = XMLState(xml_data)
        volume_type = namedtuple(
            'volume_type', [
                'name',
                'size',
                'realpath',
                'mountpoint',
                'fullsize',
                'label',
                'attributes',
                'is_root_volume'
            ]
        )
        assert state.get_volumes() == [
            volume_type(
                name='usr', size=None, realpath='usr',
                mountpoint='usr', fullsize=True,
                label=None,
                attributes=[],
                is_root_volume=False
            ),
            volume_type(
                name='LVRoot', size='freespace:30', realpath='/',
                mountpoint=None, fullsize=False,
                label=None,
                attributes=[],
                is_root_volume=True
            ),
            volume_type(
                name='LVSwap', size='size:128',
                realpath='swap',
                mountpoint=None, fullsize=False,
                label='SWAP',
                attributes=[],
                is_root_volume=False
            )
        ]

    @patch('kiwi.xml_state.XMLState.get_build_type_system_disk_section')
    def test_get_empty_volumes(self, mock_system_disk):
        mock_system_disk.return_value = None
        assert self.state.get_volumes() == []

    def test_get_strip_files_to_delete(self):
        assert self.state.get_strip_files_to_delete() == ['del-a', 'del-b']

    def test_get_strip_tools_to_keep(self):
        assert self.state.get_strip_tools_to_keep() == ['tool-a', 'tool-b']

    def test_get_strip_libraries_to_keep(self):
        assert self.state.get_strip_libraries_to_keep() == ['lib-a', 'lib-b']

    def test_get_build_type_machine_section(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxSimpleFlavour'], 'oem')
        assert state.get_build_type_machine_section().get_guestOS() == 'suse'

    def test_get_drivers_list(self):
        assert self.state.get_drivers_list() == \
            ['crypto/*', 'drivers/acpi/*', 'bar']

    def test_get_build_type_oemconfig_section(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, None, 'oem')
        assert state.get_build_type_oemconfig_section().get_oem_swap()[0] is \
            True

    def test_get_oemconfig_oem_resize(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'oem')
        assert state.get_oemconfig_oem_resize() is True
        description = XMLDescription(
            '../data/example_multiple_users_config.xml'
        )
        xml_data = description.load()
        state = XMLState(xml_data)
        assert state.get_oemconfig_oem_resize() is False

    def test_get_oemconfig_oem_multipath_scan(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'oem')
        assert state.get_oemconfig_oem_multipath_scan() is False
        description = XMLDescription(
            '../data/example_disk_config.xml'
        )
        xml_data = description.load()
        state = XMLState(xml_data)
        assert state.get_oemconfig_oem_multipath_scan() is False

    def test_get_oemconfig_swap_mbytes(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['containerFlavour'], 'docker')
        assert state.get_oemconfig_swap_mbytes() is None
        state = XMLState(xml_data, ['vmxFlavour'], 'oem')
        assert state.get_oemconfig_swap_mbytes() == 42

    def test_get_oemconfig_swap_name(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['containerFlavour'], 'docker')
        assert state.get_oemconfig_swap_name() == 'LVSwap'
        state = XMLState(xml_data, ['vmxFlavour'], 'oem')
        assert state.get_oemconfig_swap_name() == 'swap'

    def test_get_oemconfig_swap_mbytes_default(self):
        description = XMLDescription(
            '../data/example_btrfs_config.xml'
        )
        xml_data = description.load()
        state = XMLState(xml_data)
        assert state.get_oemconfig_swap_mbytes() == 128

    def test_get_users_sections(self):
        assert self.state.get_users_sections()[0].get_user()[0].get_name() == \
            'root'

    def test_get_users(self):
        description = XMLDescription(
            '../data/example_multiple_users_config.xml'
        )
        xml_data = description.load()
        state = XMLState(xml_data)
        users = state.get_users()
        assert len(users) == 3
        assert any(u.get_name() == 'root' for u in users)
        assert any(u.get_name() == 'tux' for u in users)
        assert any(u.get_name() == 'kiwi' for u in users)

    def test_get_user_groups(self):
        description = XMLDescription(
            '../data/example_multiple_users_config.xml'
        )
        xml_data = description.load()
        state = XMLState(xml_data)

        assert len(state.get_user_groups('root')) == 0
        assert len(state.get_user_groups('tux')) == 1
        assert any(grp == 'users' for grp in state.get_user_groups('tux'))
        assert len(state.get_user_groups('kiwi')) == 3
        assert any(grp == 'users' for grp in state.get_user_groups('kiwi'))
        assert any(grp == 'kiwi' for grp in state.get_user_groups('kiwi'))
        assert any(grp == 'admin' for grp in state.get_user_groups('kiwi'))

    def test_copy_displayname(self):
        self.state.copy_displayname(self.boot_state)
        assert self.boot_state.xml_data.get_displayname() == 'Bob'

    def test_copy_drivers_sections(self):
        self.state.copy_drivers_sections(self.boot_state)
        assert 'bar' in self.boot_state.get_drivers_list()

    def test_copy_systemdisk_section(self):
        self.state.copy_systemdisk_section(self.boot_state)
        systemdisk = self.boot_state.get_build_type_system_disk_section()
        assert systemdisk.get_name() == 'mydisk'

    @patch('kiwi.xml_parse.type_.get_bootloader')
    def test_copy_bootloader_section(self, mock_bootloader):
        mock_bootloader.return_value = [self.bootloader]
        self.state.copy_bootloader_section(self.boot_state)
        assert self.boot_state.get_build_type_bootloader_section() == \
            self.bootloader

    def test_copy_strip_sections(self):
        self.state.copy_strip_sections(self.boot_state)
        assert 'del-a' in self.boot_state.get_strip_files_to_delete()

    def test_copy_machine_section(self):
        self.state.copy_machine_section(self.boot_state)
        machine = self.boot_state.get_build_type_machine_section()
        assert machine.get_memory() == 512

    def test_copy_oemconfig_section(self):
        self.state.copy_oemconfig_section(self.boot_state)
        oemconfig = self.boot_state.get_build_type_oemconfig_section()
        assert oemconfig.get_oem_systemsize()[0] == 2048

    def test_copy_repository_sections(self):
        self.state.copy_repository_sections(self.boot_state, True)
        repository = self.boot_state.get_repository_sections()[0]
        assert repository.get_source().get_path() == 'iso:///image/CDs/dvd.iso'

    def test_copy_preferences_subsections(self):
        self.state.copy_preferences_subsections(
            ['bootsplash_theme'], self.boot_state
        )
        preferences = self.boot_state.get_preferences_sections()[0]
        assert preferences.get_bootsplash_theme()[0] == 'openSUSE'

    def test_copy_build_type_attributes(self):
        self.state.copy_build_type_attributes(
            ['firmware'], self.boot_state
        )
        assert self.boot_state.build_type.get_firmware() == 'efi'

    def test_copy_bootincluded_packages_with_no_image_packages(self):
        self.state.copy_bootincluded_packages(self.boot_state)
        bootstrap_packages = self.boot_state.get_bootstrap_packages()
        assert 'plymouth-branding-openSUSE' in bootstrap_packages
        assert 'grub2-branding-openSUSE' in bootstrap_packages
        assert 'gfxboot-branding-openSUSE' in bootstrap_packages
        to_delete_packages = self.boot_state.get_to_become_deleted_packages()
        assert 'gfxboot-branding-openSUSE' not in to_delete_packages

    def test_copy_bootincluded_packages_with_image_packages(self):
        boot_description = XMLDescription(
            '../data/isoboot/example-distribution/config.xml'
        )
        boot_state = XMLState(boot_description.load(), ['std'])
        self.state.copy_bootincluded_packages(boot_state)
        image_packages = boot_state.get_system_packages()
        assert 'plymouth-branding-openSUSE' in image_packages
        assert 'grub2-branding-openSUSE' in image_packages
        assert 'gfxboot-branding-openSUSE' in image_packages
        to_delete_packages = boot_state.get_to_become_deleted_packages()
        assert 'gfxboot-branding-openSUSE' not in to_delete_packages

    def test_copy_bootincluded_archives(self):
        self.state.copy_bootincluded_archives(self.boot_state)
        bootstrap_archives = self.boot_state.get_bootstrap_archives()
        assert '/absolute/path/to/image.tgz' in bootstrap_archives

    def test_copy_bootdelete_packages(self):
        self.state.copy_bootdelete_packages(self.boot_state)
        to_delete_packages = self.boot_state.get_to_become_deleted_packages()
        assert 'vim' in to_delete_packages

    def test_copy_bootdelete_packages_no_delete_section_in_boot_descr(self):
        boot_description = XMLDescription(
            '../data/isoboot/example-distribution-no-delete-section/config.xml'
        )
        boot_state = XMLState(
            boot_description.load()
        )
        self.state.copy_bootdelete_packages(boot_state)
        to_delete_packages = boot_state.get_to_become_deleted_packages()
        assert 'vim' in to_delete_packages

    def test_build_type_size(self):
        result = self.state.get_build_type_size()
        assert result.mbytes == 1024
        assert result.additive

    def test_build_type_size_with_unpartitioned(self):
        state = XMLState(self.description.load(), ['vmxSimpleFlavour'], 'oem')
        result = state.get_build_type_size()
        assert result.mbytes == 3072
        assert not result.additive
        result = state.get_build_type_size(include_unpartitioned=True)
        assert result.mbytes == 4096
        assert not result.additive

    def test_get_build_type_unpartitioned_bytes(self):
        assert self.state.get_build_type_unpartitioned_bytes() == 0
        state = XMLState(self.description.load(), ['vmxSimpleFlavour'], 'oem')
        assert state.get_build_type_unpartitioned_bytes() == 1073741824
        state = XMLState(self.description.load(), ['vmxFlavour'], 'oem')
        assert state.get_build_type_unpartitioned_bytes() == 0
        state = XMLState(self.description.load(), ['ec2Flavour'], 'oem')
        assert state.get_build_type_unpartitioned_bytes() == 0

    def test_get_volume_group_name(self):
        assert self.state.get_volume_group_name() == 'mydisk'

    def test_get_volume_group_name_default(self):
        assert self.boot_state.get_volume_group_name() == 'systemVG'

    def test_get_distribution_name_from_boot_attribute(self):
        assert self.state.get_distribution_name_from_boot_attribute() == \
            'distribution'

    def test_get_fs_mount_option_list(self):
        assert self.state.get_fs_mount_option_list() == ['async']

    def test_get_fs_create_option_list(self):
        assert self.state.get_fs_create_option_list() == ['-O', '^has_journal']

    @patch('kiwi.xml_parse.type_.get_boot')
    def test_get_distribution_name_from_boot_attribute_no_boot(self, mock_boot):
        mock_boot.return_value = None
        with raises(KiwiDistributionNameError):
            self.state.get_distribution_name_from_boot_attribute()

    @patch('kiwi.xml_parse.type_.get_boot')
    def test_get_distribution_name_from_boot_attribute_invalid_boot(
        self, mock_boot
    ):
        mock_boot.return_value = 'invalid'
        with raises(KiwiDistributionNameError):
            self.state.get_distribution_name_from_boot_attribute()

    def test_delete_repository_sections(self):
        self.state.delete_repository_sections()
        assert self.state.get_repository_sections() == []

    def test_delete_repository_sections_used_for_build(self):
        self.state.delete_repository_sections_used_for_build()
        assert self.state.get_repository_sections()[0].get_imageonly()

    def test_get_build_type_vmconfig_entries(self):
        assert self.state.get_build_type_vmconfig_entries() == []

    def test_get_build_type_vmconfig_entries_for_simple_disk(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxSimpleFlavour'], 'oem')
        assert state.get_build_type_vmconfig_entries() == [
            'numvcpus = "4"', 'cpuid.coresPerSocket = "2"'
        ]

    def test_get_build_type_vmconfig_entries_no_machine_section(self):
        description = XMLDescription('../data/example_disk_config.xml')
        xml_data = description.load()
        state = XMLState(xml_data)
        assert state.get_build_type_vmconfig_entries() == []

    def test_get_build_type_docker_containerconfig_section(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['containerFlavour'], 'docker')
        containerconfig = state.get_build_type_containerconfig_section()
        assert containerconfig.get_name() == \
            'container_name'
        assert containerconfig.get_maintainer() == \
            'tux'
        assert containerconfig.get_workingdir() == \
            '/root'

    def test_set_container_tag(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['containerFlavour'], 'docker')
        state.set_container_config_tag('new_tag')
        config = state.get_container_config()
        assert config['container_tag'] == 'new_tag'

    def test_add_container_label(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['containerFlavour'], 'docker')
        state.add_container_config_label('somelabel', 'overwrittenvalue')
        state.add_container_config_label('new_label', 'new value')
        config = state.get_container_config()
        assert config['labels'] == {
            'somelabel': 'overwrittenvalue',
            'someotherlabel': 'anotherlabelvalue',
            'new_label': 'new value'
        }

    def test_add_container_label_without_contianerconfig(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['xenDom0Flavour'], 'docker')
        state.add_container_config_label('somelabel', 'newlabelvalue')
        config = state.get_container_config()
        assert config['labels'] == {
            'somelabel': 'newlabelvalue'
        }

    def test_add_container_label_no_container_image_type(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'oem')
        state.add_container_config_label('somelabel', 'newlabelvalue')
        with self._caplog.at_level(logging.WARNING):
            config = state.get_container_config()
            assert config == {
                'history': {'author': 'Marcus <ms@suse.com>'},
                'maintainer': 'Marcus <ms@suse.com>'
            }

    def test_set_container_tag_not_applied(self):
        with self._caplog.at_level(logging.WARNING):
            self.state.set_container_config_tag('new_tag')

    def test_get_container_config(self):
        expected_config = {
            'labels': {
                'somelabel': 'labelvalue',
                'someotherlabel': 'anotherlabelvalue'
            },
            'maintainer': 'tux',
            'entry_subcommand': ['ls', '-l'],
            'container_name': 'container_name',
            'container_tag': 'container_tag',
            'additional_tags': ['current', 'foobar'],
            'workingdir': '/root',
            'environment': {
                'PATH': '/bin:/usr/bin:/home/user/bin',
                'SOMEVAR': 'somevalue'
            },
            'user': 'root',
            'volumes': ['/tmp', '/var/log'],
            'entry_command': ['/bin/bash', '-x'],
            'expose_ports': ['80', '8080'],
            'history': {
                'author': 'history author',
                'comment': 'This is a comment',
                'created_by': 'created by text',
                'application_id': '123',
                'package_version': '2003.12.0.0',
                'launcher': 'app'
            }
        }
        xml_data = self.description.load()
        state = XMLState(xml_data, ['containerFlavour'], 'docker')
        assert state.get_container_config() == expected_config

    def test_get_container_config_clear_commands(self):
        expected_config = {
            'maintainer': 'tux',
            'entry_subcommand': [],
            'container_name': 'container_name',
            'container_tag': 'container_tag',
            'workingdir': '/root',
            'user': 'root',
            'entry_command': [],
            'history': {'author': 'Marcus <ms@suse.com>'}
        }
        xml_data = self.description.load()
        state = XMLState(xml_data, ['derivedContainer'], 'docker')
        assert state.get_container_config() == expected_config

    def test_get_spare_part(self):
        assert self.state.get_build_type_spare_part_size() == 200
        assert self.state.get_build_type_spare_part_fs_attributes() == [
            'no-copy-on-write'
        ]

    def test_get_build_type_format_options(self):
        assert self.state.get_build_type_format_options() == {
            'super': 'man',
            'force_size': None
        }

    def test_get_derived_from_image_uri(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['derivedContainer'], 'docker')
        assert state.get_derived_from_image_uri().uri == \
            'obs://project/repo/image#mytag'

    def test_set_derived_from_image_uri(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['derivedContainer'], 'docker')
        state.set_derived_from_image_uri('file:///new_uri')
        assert state.get_derived_from_image_uri().translate() == '/new_uri'

    def test_set_derived_from_image_uri_not_applied(self):
        with self._caplog.at_level(logging.WARNING):
            self.state.set_derived_from_image_uri('file:///new_uri')

    def test_is_xen_server(self):
        assert self.state.is_xen_server() is True

    def test_is_xen_guest_by_machine_setup(self):
        assert self.state.is_xen_guest() is True

    def test_is_xen_guest_no_xen_guest_setup(self):
        assert self.boot_state.is_xen_guest() is False

    @patch('platform.machine')
    def test_is_xen_guest_by_firmware_setup(self, mock_platform_machine):
        mock_platform_machine.return_value = 'x86_64'
        xml_data = self.description.load()
        state = XMLState(xml_data, ['ec2Flavour'], 'oem')
        assert state.is_xen_guest() is True

    @patch('platform.machine')
    def test_is_xen_guest_by_architecture(self, mock_platform_machine):
        mock_platform_machine.return_value = 'unsupported'
        xml_data = self.description.load()
        state = XMLState(xml_data, ['ec2Flavour'], 'oem')
        assert state.is_xen_guest() is False

    def test_get_initrd_system(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'oem')
        assert state.get_initrd_system() == 'dracut'
        state = XMLState(xml_data, ['vmxSimpleFlavour'], 'iso')
        assert state.get_initrd_system() == 'dracut'
        state = XMLState(xml_data, ['containerFlavour'], 'docker')
        assert state.get_initrd_system() is None
        state = XMLState(xml_data, [], 'oem')
        assert state.get_initrd_system() == 'dracut'

    def test_get_rpm_locale_filtering(self):
        assert self.state.get_rpm_locale_filtering() is True
        assert self.boot_state.get_rpm_locale_filtering() is False

    def test_get_locale(self):
        assert self.state.get_locale() == ['en_US', 'de_DE']
        assert self.boot_state.get_locale() is None

    def test_get_rpm_locale(self):
        assert self.state.get_rpm_locale() == [
            'POSIX', 'C', 'C.UTF-8', 'en_US', 'de_DE'
        ]
        assert self.boot_state.get_rpm_locale() is None

    def test_set_root_partition_uuid(self):
        assert self.state.get_root_partition_uuid() is None
        self.state.set_root_partition_uuid('some-id')
        assert self.state.get_root_partition_uuid() == 'some-id'

    def test_set_root_filesystem_uuid(self):
        assert self.state.get_root_filesystem_uuid() is None
        self.state.set_root_filesystem_uuid('some-id')
        assert self.state.get_root_filesystem_uuid() == 'some-id'

    @patch('kiwi.xml_parse.type_.get_bootloader')
    def test_get_build_type_bootloader_name(self, mock_bootloader):
        mock_bootloader.return_value = [None]
        assert self.state.get_build_type_bootloader_name() == 'grub2'
        mock_bootloader.return_value = [self.bootloader]
        assert self.state.get_build_type_bootloader_name() == 'some-loader'

    @patch('kiwi.xml_parse.type_.get_bootloader')
    def test_get_build_type_bootloader_console(self, mock_bootloader):
        mock_bootloader.return_value = [self.bootloader]
        assert self.state.get_build_type_bootloader_console() == \
            'some-console'

    @patch('kiwi.xml_parse.type_.get_bootloader')
    def test_get_build_type_bootloader_serial_line_setup(self, mock_bootloader):
        mock_bootloader.return_value = [self.bootloader]
        assert self.state.get_build_type_bootloader_serial_line_setup() == \
            'some-serial'
        mock_bootloader.return_value = [None]
        assert self.state.get_build_type_bootloader_serial_line_setup() \
            is None

    @patch('kiwi.xml_parse.type_.get_bootloader')
    def test_get_build_type_bootloader_timeout(self, mock_bootloader):
        mock_bootloader.return_value = [self.bootloader]
        assert self.state.get_build_type_bootloader_timeout() == \
            'some-timeout'

    @patch('kiwi.xml_parse.type_.get_bootloader')
    def test_get_build_type_bootloader_timeout_style(self, mock_bootloader):
        mock_bootloader.return_value = [self.bootloader]
        assert self.state.get_build_type_bootloader_timeout_style() == \
            'some-style'
        mock_bootloader.return_value = [None]
        assert self.state.get_build_type_bootloader_timeout_style() \
            is None

    @patch('kiwi.xml_parse.type_.get_bootloader')
    def test_get_build_type_bootloader_targettype(self, mock_bootloader):
        mock_bootloader.return_value = [self.bootloader]
        assert self.state.get_build_type_bootloader_targettype() == \
            'some-target'
