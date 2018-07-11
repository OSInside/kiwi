from mock import patch

from .test_helper import raises

from kiwi.xml_state import XMLState
from kiwi.xml_description import XMLDescription
from kiwi.exceptions import (
    KiwiTypeNotFound,
    KiwiDistributionNameError,
    KiwiProfileNotFound
)
from collections import namedtuple


class TestXMLState(object):
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

    def test_build_type_primary_selected(self):
        assert self.state.get_build_type_name() == 'oem'

    def test_build_type_first_selected(self):
        self.state.xml_data.get_preferences()[1].get_type()[0].set_primary(
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

    def test_get_image_version(self):
        assert self.state.get_image_version() == '1.13.2'

    def test_get_bootstrap_packages(self):
        assert self.state.get_bootstrap_packages() == [
            'filesystem', 'zypper'
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
        assert self.state.xml_data.get_repository()[0].get_imageinclude() is True
        assert self.state.xml_data.get_repository()[0].get_package_gpgcheck() is False

    def test_add_repository(self):
        self.state.add_repository('repo', 'type', 'alias', 1, True)
        assert self.state.xml_data.get_repository()[3].get_source().get_path() \
            == 'repo'
        assert self.state.xml_data.get_repository()[3].get_type() == 'type'
        assert self.state.xml_data.get_repository()[3].get_alias() == 'alias'
        assert self.state.xml_data.get_repository()[3].get_priority() == 1
        assert self.state.xml_data.get_repository()[3].get_imageinclude() is True

    def test_add_repository_with_empty_values(self):
        self.state.add_repository('repo', 'type', '', '', True)
        assert self.state.xml_data.get_repository()[3].get_source().get_path() \
            == 'repo'
        assert self.state.xml_data.get_repository()[3].get_type() == 'type'
        assert self.state.xml_data.get_repository()[3].get_alias() == ''
        assert self.state.xml_data.get_repository()[3].get_priority() is None
        assert self.state.xml_data.get_repository()[3].get_imageinclude() is True

    def test_get_to_become_deleted_packages(self):
        assert self.state.get_to_become_deleted_packages() == [
            'kernel-debug'
        ]

    def test_get_build_type_vagrant_config_section(self):
        vagrant_config = self.state.get_build_type_vagrant_config_section()
        assert vagrant_config.get_provider() == 'libvirt'

    def test_get_build_type_system_disk_section(self):
        assert self.state.get_build_type_system_disk_section().get_name() == \
            'mydisk'

    def test_get_build_type_vmdisk_section(self):
        assert self.state.get_build_type_vmdisk_section().get_id() == 0

    def test_get_build_type_vmnic_entries(self):
        assert self.state.get_build_type_vmnic_entries()[0].get_interface() \
            == ''
        assert self.boot_state.get_build_type_vmnic_entries() == []

    def test_get_build_type_vmdvd_section(self):
        assert self.state.get_build_type_vmdvd_section().get_id() == 0

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
        state = XMLState(xml_data, ['vmxFlavour'], 'vmx')
        assert state.get_build_type_name() == 'vmx'

    @raises(KiwiTypeNotFound)
    def test_build_type_not_found(self):
        xml_data = self.description.load()
        XMLState(xml_data, ['vmxFlavour'], 'foo')

    @raises(KiwiTypeNotFound)
    def test_build_type_not_found_no_default_type(self):
        description = XMLDescription('../data/example_no_default_type.xml')
        xml_data = description.load()
        XMLState(xml_data, ['minimal'])

    @raises(KiwiProfileNotFound)
    def test_profile_not_found(self):
        xml_data = self.description.load()
        XMLState(xml_data, ['foo'])

    def test_profile_requires(self):
        xml_data = self.description.load()
        xml_state = XMLState(xml_data, ['composedProfile'])
        assert xml_state.profiles == [
            'composedProfile', 'vmxFlavour', 'xenFlavour'
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
                'attributes'
            ]
        )
        assert state.get_volumes() == [
            volume_type(
                name='usr_lib', size='size:1024',
                realpath='usr/lib',
                mountpoint='usr/lib', fullsize=False,
                label='library',
                attributes=[]
            ),
            volume_type(
                name='LVRoot', size='freespace:500',
                realpath='/',
                mountpoint=None, fullsize=False,
                label=None,
                attributes=[]
            ),
            volume_type(
                name='etc_volume', size='freespace:30',
                realpath='etc',
                mountpoint='etc', fullsize=False,
                label=None,
                attributes=['no-copy-on-write']
            ),
            volume_type(
                name='bin_volume', size=None,
                realpath='/usr/bin',
                mountpoint='/usr/bin', fullsize=True,
                label=None,
                attributes=[]
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
                'attributes'
            ]
        )
        assert state.get_volumes() == [
            volume_type(
                name='LVRoot', size=None, realpath='/',
                mountpoint=None, fullsize=True,
                label=None,
                attributes=[]
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
                'attributes'
            ]
        )
        assert state.get_volumes() == [
            volume_type(
                name='usr', size=None, realpath='usr',
                mountpoint='usr', fullsize=True,
                label=None,
                attributes=[]
            ),
            volume_type(
                name='LVRoot', size='freespace:30', realpath='/',
                mountpoint=None, fullsize=False,
                label=None,
                attributes=[]
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
        state = XMLState(xml_data, None, 'vmx')
        assert state.get_build_type_machine_section().get_guestOS() == 'suse'

    def test_get_build_type_pxedeploy_section(self):
        description = XMLDescription('../data/example_pxe_config.xml')
        xml_data = description.load()
        state = XMLState(xml_data, None, 'pxe')
        assert state.get_build_type_pxedeploy_section().get_server() == \
            '192.168.100.2'

    def test_get_drivers_list(self):
        assert self.state.get_drivers_list() == \
            ['crypto/*', 'drivers/acpi/*', 'bar']

    def test_get_build_type_oemconfig_section(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, None, 'oem')
        assert state.get_build_type_oemconfig_section().get_oem_swap()[0] is \
            True

    def test_get_users_sections(self):
        assert self.state.get_users_sections()[0].get_user()[0].get_name() == \
            'root'

    def test_get_users(self):
        description = XMLDescription('../data/example_multiple_users_config.xml')
        xml_data = description.load()
        state = XMLState(xml_data)
        users = state.get_users()
        assert len(users) == 3
        assert any(u.get_name() == 'root' for u in users)
        assert any(u.get_name() == 'tux' for u in users)
        assert any(u.get_name() == 'kiwi' for u in users)

    def test_get_user_groups(self):
        description = XMLDescription('../data/example_multiple_users_config.xml')
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
        state = XMLState(self.description.load(), ['vmxFlavour'], 'vmx')
        result = state.get_build_type_size()
        assert result.mbytes == 3072
        assert not result.additive
        result = state.get_build_type_size(include_unpartitioned=True)
        assert result.mbytes == 4096
        assert not result.additive

    def test_get_build_type_unpartitioned_bytes(self):
        assert self.state.get_build_type_unpartitioned_bytes() == 0
        state = XMLState(self.description.load(), ['vmxFlavour'], 'vmx')
        assert state.get_build_type_unpartitioned_bytes() == 1073741824
        state = XMLState(self.description.load(), ['vmxFlavour'], 'oem')
        assert state.get_build_type_unpartitioned_bytes() == 0
        state = XMLState(self.description.load(), ['ec2Flavour'], 'vmx')
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

    @raises(KiwiDistributionNameError)
    @patch('kiwi.xml_parse.type_.get_boot')
    def test_get_distribution_name_from_boot_attribute_no_boot(self, mock_boot):
        mock_boot.return_value = None
        self.state.get_distribution_name_from_boot_attribute()

    @raises(KiwiDistributionNameError)
    @patch('kiwi.xml_parse.type_.get_boot')
    def test_get_distribution_name_from_boot_attribute_invalid_boot(
        self, mock_boot
    ):
        mock_boot.return_value = 'invalid'
        self.state.get_distribution_name_from_boot_attribute()

    def test_delete_repository_sections(self):
        self.state.delete_repository_sections()
        assert self.state.get_repository_sections() == []

    def test_delete_repository_sections_used_for_build(self):
        self.state.delete_repository_sections_used_for_build()
        assert self.state.get_repository_sections()[0].get_imageonly()

    def test_get_build_type_vmconfig_entries(self):
        assert self.state.get_build_type_vmconfig_entries() == []

    def test_get_build_type_vmconfig_entries_for_vmx_type(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'vmx')
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
        state = XMLState(xml_data, ['vmxFlavour'], 'docker')
        containerconfig = state.get_build_type_containerconfig_section()
        assert containerconfig.get_name() == \
            'container_name'
        assert containerconfig.get_maintainer() == \
            'tux'
        assert containerconfig.get_workingdir() == \
            '/root'

    def test_set_container_tag(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'docker')
        state.set_container_config_tag('new_tag')
        config = state.get_container_config()
        assert config['container_tag'] == 'new_tag'

    def test_add_container_label(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'docker')
        state.add_container_config_label('somelabel', 'overwrittenvalue')
        state.add_container_config_label('new_label', 'new value')
        config = state.get_container_config()
        assert config['labels'] == [
            '--config.label=somelabel=overwrittenvalue',
            '--config.label=someotherlabel=anotherlabelvalue',
            '--config.label=new_label=new value'
        ]

    def test_add_container_label_without_contianerconfig(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['xenFlavour'], 'docker')
        state.add_container_config_label('somelabel', 'newlabelvalue')
        config = state.get_container_config()
        assert config['labels'] == [
            '--config.label=somelabel=newlabelvalue'
        ]

    @patch('kiwi.logger.log.warning')
    def test_add_container_label_no_contianer_image_type(self, mock_log_warn):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'vmx')
        state.add_container_config_label('somelabel', 'newlabelvalue')
        config = state.get_container_config()
        assert not config
        assert mock_log_warn.called

    @patch('kiwi.logger.log.warning')
    def test_set_container_tag_not_applied(self, mock_log_warn):
        self.state.set_container_config_tag('new_tag')
        assert mock_log_warn.called

    def test_get_container_config(self):
        expected_config = {
            'labels': [
                '--config.label=somelabel=labelvalue',
                '--config.label=someotherlabel=anotherlabelvalue'
            ],
            'maintainer': ['--author=tux'],
            'entry_subcommand': [
                '--config.cmd=ls',
                '--config.cmd=-l'
            ],
            'container_name': 'container_name',
            'container_tag': 'container_tag',
            'additional_tags': ['current', 'foobar'],
            'workingdir': ['--config.workingdir=/root'],
            'environment': [
                '--config.env=PATH=/bin:/usr/bin:/home/user/bin',
                '--config.env=SOMEVAR=somevalue'
            ],
            'user': ['--config.user=root'],
            'volumes': [
                '--config.volume=/tmp',
                '--config.volume=/var/log'
            ],
            'entry_command': [
                '--config.entrypoint=/bin/bash',
                '--config.entrypoint=-x'
            ],
            'expose_ports': [
                '--config.exposedports=80',
                '--config.exposedports=8080'
            ]
        }
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'docker')
        assert state.get_container_config() == expected_config

    def test_get_container_config_clear_commands(self):
        expected_config = {
            'maintainer': ['--author=tux'],
            'entry_subcommand': [
                '--clear=config.cmd'
            ],
            'container_name': 'container_name',
            'container_tag': 'container_tag',
            'workingdir': ['--config.workingdir=/root'],
            'user': ['--config.user=root'],
            'entry_command': [
                '--clear=config.entrypoint',
            ]
        }
        xml_data = self.description.load()
        state = XMLState(xml_data, ['derivedContainer'], 'docker')
        assert state.get_container_config() == expected_config

    def test_get_spare_part(self):
        assert self.state.get_build_type_spare_part_size() == 200

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

    @patch('kiwi.logger.log.warning')
    def test_set_derived_from_image_uri_not_applied(self, mock_log_warn):
        self.state.set_derived_from_image_uri('file:///new_uri')
        assert mock_log_warn.called

    def test_is_xen_server(self):
        assert self.state.is_xen_server() is True

    def test_is_xen_guest_by_machine_setup(self):
        assert self.state.is_xen_guest() is True

    def test_is_xen_guest_by_firmware_setup(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['ec2Flavour'], 'vmx')
        assert state.is_xen_guest() is True

    def test_get_initrd_system(self):
        xml_data = self.description.load()
        state = XMLState(xml_data, ['vmxFlavour'], 'vmx')
        assert state.get_initrd_system() == 'dracut'
        state = XMLState(xml_data, ['vmxFlavour'], 'iso')
        assert state.get_initrd_system() == 'dracut'
        state = XMLState(xml_data, ['vmxFlavour'], 'docker')
        assert state.get_initrd_system() is None
        state = XMLState(xml_data, [], 'oem')
        assert state.get_initrd_system() == 'kiwi'
