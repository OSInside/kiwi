from kiwi.storage.subformat.template.ova_compose import OvaComposeTemplate


class TestOvaComposeTemplate:
    """Test OvaComposeTemplate hardware configuration"""

    def test_get_template_with_default_hardware(self):
        """Test template generation with default hardware (ide + VmxNet3)"""
        template = OvaComposeTemplate().get_template()
        rendered = template.substitute({
            'display_name': 'test-vm',
            'guest_os': 'other4xLinux64Guest',
            'firmware': 'bios',
            'secure_boot': 'false',
            'number_of_cpus': 2,
            'memory_size': 4096,
            'vmdk_file': 'test.vmdk',
            'virtual_hardware_version': '9'
        })

        # Verify default hardware configuration (ide controller)
        assert 'parent: ide0' in rendered
        assert 'subtype: VmxNet3' in rendered
        assert 'rootdisk:' in rendered
        assert 'ethernet0:' in rendered

    def test_get_template_with_lsilogic_controller(self):
        """Test template generation with SCSI lsilogic controller"""
        template = OvaComposeTemplate().get_template(
            disk_controller='lsilogic'
        )
        rendered = template.substitute({
            'display_name': 'test-vm',
            'guest_os': 'other4xLinux64Guest',
            'firmware': 'bios',
            'secure_boot': 'false',
            'number_of_cpus': 2,
            'memory_size': 4096,
            'vmdk_file': 'test.vmdk',
            'virtual_hardware_version': '9'
        })

        # Verify lsilogic mapping to scsi0
        assert 'parent: scsi0' in rendered

    def test_get_template_with_sata_controller(self):
        """Test template generation with SATA controller"""
        template = OvaComposeTemplate().get_template(
            disk_controller='sata'
        )
        rendered = template.substitute({
            'display_name': 'test-vm',
            'guest_os': 'other4xLinux64Guest',
            'firmware': 'bios',
            'secure_boot': 'false',
            'number_of_cpus': 2,
            'memory_size': 4096,
            'vmdk_file': 'test.vmdk',
            'virtual_hardware_version': '9'
        })

        # Verify sata mapping
        assert 'parent: sata0' in rendered

    def test_get_template_with_nvme_controller(self):
        """Test template generation with NVMe controller"""
        template = OvaComposeTemplate().get_template(
            disk_controller='nvme'
        )
        rendered = template.substitute({
            'display_name': 'test-vm',
            'guest_os': 'other4xLinux64Guest',
            'firmware': 'bios',
            'secure_boot': 'false',
            'number_of_cpus': 2,
            'memory_size': 4096,
            'vmdk_file': 'test.vmdk',
            'virtual_hardware_version': '9'
        })

        # Verify nvme mapping
        assert 'parent: nvme0' in rendered

    def test_get_template_with_e1000_nic_driver(self):
        """Test template generation with e1000 network driver"""
        template = OvaComposeTemplate().get_template(
            network_setup={
                '0': {'driver': 'e1000', 'connection_type': 'bridged', 'mac': 'generated'}
            }
        )
        rendered = template.substitute({
            'display_name': 'test-vm',
            'guest_os': 'other4xLinux64Guest',
            'firmware': 'bios',
            'secure_boot': 'false',
            'number_of_cpus': 2,
            'memory_size': 4096,
            'vmdk_file': 'test.vmdk',
            'virtual_hardware_version': '9'
        })

        # Verify e1000 driver
        assert 'subtype: e1000' in rendered

    def test_get_template_with_multiple_configurations(self):
        """Test template generation with both custom disk and nic config"""
        template = OvaComposeTemplate().get_template(
            disk_controller='lsilogic',
            memory_setup=True,
            cpu_setup=True,
            network_setup={
                '0': {'driver': 'e1000', 'connection_type': 'bridged', 'mac': 'generated'}
            }
        )
        rendered = template.substitute({
            'display_name': 'test-vm',
            'guest_os': 'suse-64',
            'firmware': 'efi',
            'secure_boot': 'true',
            'number_of_cpus': 4,
            'memory_size': 8192,
            'vmdk_file': 'test.vmdk',
            'virtual_hardware_version': '9'
        })

        # Verify both configurations are applied
        assert 'parent: scsi0' in rendered
        assert 'subtype: e1000' in rendered
        assert 'cpus: 4' in rendered
        assert 'memory: 8192' in rendered
        assert 'os_vmw: "suse-64"' in rendered

    def test_get_template_controller_mapping(self):
        """Test all supported disk controller mappings"""
        controller_mappings = {
            'ide': 'ide0',
            'sata': 'sata0',
            'scsi': 'scsi0',
            'lsilogic': 'scsi0',
            'lsisas1068': 'scsi0',
            'nvme': 'nvme0',
            'paravirtual': 'scsi0'
        }

        for controller, expected_parent in controller_mappings.items():
            template = OvaComposeTemplate().get_template(
                disk_controller=controller
            )
            rendered = template.substitute({
                'display_name': 'test-vm',
                'guest_os': 'other4xLinux64Guest',
                'firmware': 'bios',
                'secure_boot': 'false',
                'number_of_cpus': 2,
                'memory_size': 4096,
                'vmdk_file': 'test.vmdk',
                'virtual_hardware_version': '9'
            })
            assert f'parent: {expected_parent}' in rendered, \
                f"Controller '{controller}' should map to '{expected_parent}'"

    def test_get_template_controller_subtype_mapping(self):
        """Test all supported disk controller subtype mappings"""
        controller_subtypes = {
            'ide': 'ide',
            'sata': 'sata',
            'scsi': 'scsi',
            'lsilogic': 'lsilogic',
            'lsisas1068': 'lsisas1068',
            'nvme': 'nvme',
            'paravirtual': 'paravirtual'
        }

        for controller, expected_subtype in controller_subtypes.items():
            template = OvaComposeTemplate().get_template(
                disk_controller=controller
            )
            rendered = template.substitute({
                'display_name': 'test-vm',
                'guest_os': 'other4xLinux64Guest',
                'firmware': 'bios',
                'secure_boot': 'false',
                'number_of_cpus': 2,
                'memory_size': 4096,
                'vmdk_file': 'test.vmdk',
                'virtual_hardware_version': '9'
            })
            assert f'subtype: {expected_subtype}' in rendered, \
                f"Controller '{controller}' should set subtype '{expected_subtype}'"

    def test_get_template_unknown_controller_defaults_to_nvme(self):
        """Test that unknown disk controllers default to nvme0"""
        template = OvaComposeTemplate().get_template(
            disk_controller='unknown_controller'
        )
        rendered = template.substitute({
            'display_name': 'test-vm',
            'guest_os': 'other4xLinux64Guest',
            'firmware': 'bios',
            'secure_boot': 'false',
            'number_of_cpus': 2,
            'memory_size': 4096,
            'vmdk_file': 'test.vmdk',
            'virtual_hardware_version': '9'
        })

        # Verify unknown controller defaults to nvme0
        assert 'parent: nvme0' in rendered
        assert 'type: nvme_controller' in rendered
        assert 'subtype: unknown_controller' in rendered

    def test_get_template_with_iso_controller_subtype(self):
        """Test that ISO controller subtype is rendered"""
        template = OvaComposeTemplate().get_template(
            iso_setup=True,
            iso_controller='lsilogic'
        )
        rendered = template.substitute({
            'display_name': 'test-vm',
            'guest_os': 'other4xLinux64Guest',
            'firmware': 'bios',
            'secure_boot': 'false',
            'number_of_cpus': 2,
            'memory_size': 4096,
            'vmdk_file': 'test.vmdk',
            'virtual_hardware_version': '9'
        })

        assert 'cdrom0:' in rendered
        assert 'parent: scsi0' in rendered
        assert 'subtype: lsilogic' in rendered

    def test_get_template_with_duplicate_controllers(self):
        """Test that duplicate controllers are deduplicated"""
        # Both disk and ISO use IDE controller - should only appear once
        template = OvaComposeTemplate().get_template(
            disk_controller='ide',
            iso_setup=True,
            iso_controller='ide'
        )
        rendered = template.substitute({
            'display_name': 'test-vm',
            'guest_os': 'other4xLinux64Guest',
            'firmware': 'bios',
            'secure_boot': 'false',
            'number_of_cpus': 2,
            'memory_size': 4096,
            'vmdk_file': 'test.vmdk',
            'virtual_hardware_version': '9'
        })

        # Count ide0 controller definitions - should appear only once
        ide_count = rendered.count('ide0:')
        assert ide_count == 1, f"IDE0 controller should appear exactly once, but appears {ide_count} times"
