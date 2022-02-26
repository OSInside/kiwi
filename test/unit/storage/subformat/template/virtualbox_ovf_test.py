from lxml import objectify

from kiwi.storage.subformat.template.virtualbox_ovf import (
    VirtualboxOvfTemplate
)


class TestVirtualboxOvfTemplate:
    def setup(self):
        self.ovf_template = VirtualboxOvfTemplate()

    def setup_method(self, cls):
        self.setup()

    def test_ovf_parameters(self):
        args = {
            'vm_name': 'jumper',
            'root_uuid': 'uuid',
            'vm_description': 'Leap 15 image',
            'disk_image_capacity': 21,
        }
        ovf_file = self.ovf_template.get_template().substitute(args)
        ovf = objectify.fromstring(ovf_file)

        for (attr, value) in ovf.DiskSection.Disk.items():
            if 'capacity' in attr:
                assert value == str(args['disk_image_capacity'])

        vm_name_attr, vm_name_value = ovf.VirtualSystem.items()[0]
        assert 'id' in vm_name_attr and vm_name_value == args['vm_name']

        cimos_id_attr, cimos_id_value = \
            ovf.VirtualSystem.OperatingSystemSection.items()[0]
        assert 'id' in cimos_id_attr and int(cimos_id_value) == 101

        assert ovf.VirtualSystem.OperatingSystemSection.Description \
            == args['vm_description']
