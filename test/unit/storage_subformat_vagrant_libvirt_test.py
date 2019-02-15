from mock import call, patch
import mock

from .test_helper import patch_open
from .storage_subformat_vagrant_base_test import TestDiskFormatVagrant

from kiwi.storage.subformat.vagrant_libvirt import DiskFormatVagrantLibVirt

from textwrap import dedent


class TestDiskFormatVagrantLibVirt(TestDiskFormatVagrant):
    def setup(self):
        super(TestDiskFormatVagrantLibVirt, self).setup()
        self.disk_format = DiskFormatVagrantLibVirt(
            self.xml_state, 'root_dir', 'target_dir',
            {'vagrantconfig': self.vagrantconfig}
        )

    def test_store_to_result(self):
        result = mock.Mock()
        self.disk_format.store_to_result(result)
        result.add.assert_called_once_with(
            compress=False,
            filename='target_dir/'
            'some-disk-image.x86_64-1.2.3.vagrant.libvirt.box',
            key='disk_format_image',
            shasum=True,
            use_for_bundle=True
        )

    @patch('kiwi.storage.subformat.vagrant_libvirt.Command.run')
    @patch('kiwi.storage.subformat.vagrant_base.mkdtemp')
    @patch('kiwi.storage.subformat.vagrant_libvirt.DiskFormatQcow2')
    @patch('kiwi.storage.subformat.vagrant_base.random.randrange')
    @patch_open
    def test_create_image_format(
        self, mock_open, mock_rand, mock_qcow, mock_mkdtemp, mock_command
    ):
        mock_rand.return_value = 0xa
        mock_mkdtemp.return_value = 'tmpdir'
        qcow = mock.Mock()
        qcow.image_format = 'qcow2'
        mock_qcow.return_value = qcow
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)
        metadata_json = dedent('''
            {
              "format": "qcow2",
              "provider": "libvirt",
              "virtual_size": "42"
            }
        ''').strip()
        vagrantfile = dedent('''
            Vagrant.configure("2") do |config|
              config.vm.base_mac = "00163E0A0A0A"
              config.vm.provider :libvirt do |libvirt|
                libvirt.driver = "kvm"
              end
            end
        ''').strip()

        self.disk_format.create_image_format()

        qcow.create_image_format.assert_called_once_with()

        assert file_mock.write.call_args_list == [
            call(metadata_json), call(vagrantfile)
        ]

        assert mock_command.call_args_list == [
            call([
                'mv', 'target_dir/some-disk-image.x86_64-1.2.3.qcow2',
                'tmpdir/box.img'
            ]),
            call([
                'tar', '-C', 'tmpdir', '-czf',
                'target_dir/some-disk-image.x86_64-1.2.3.vagrant.libvirt.box',
                'metadata.json', 'Vagrantfile', 'box.img'
            ])
        ]
