from mock import call, patch
import mock

from .test_helper import patch_open, raises

from kiwi.exceptions import KiwiFormatSetupError
from kiwi.storage.subformat.vagrant_base import DiskFormatVagrantBase

from textwrap import dedent


class DiskFormatVagrantgMock(DiskFormatVagrantBase):

    FILES = ["one_file", "two_file", "red_file", "blue_file"]

    def create_box_img(self, tmp_dir):
        return self.FILES

    def vagrant_post_init(self):
        self.provider = 'dummy'
        self.image_format = 'vagrant.dummy.box'


class TestDiskFormatVagrant(object):
    def setup(self):
        xml_data = mock.Mock()
        xml_data.get_name = mock.Mock(
            return_value='some-disk-image'
        )
        self.xml_state = mock.Mock()
        self.xml_state.xml_data = xml_data
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.vagrantconfig = mock.Mock()
        self.vagrantconfig.get_virtualsize = mock.Mock(
            return_value=42
        )


class TestDiskFormatVagrantBase(TestDiskFormatVagrant):

    def setup(self):
        super(TestDiskFormatVagrantBase, self).setup()
        self.disk_format = DiskFormatVagrantBase(
            self.xml_state, 'root_dir', 'target_dir',
            {'vagrantconfig': self.vagrantconfig}
        )

    @raises(NotImplementedError)
    def test_create_box_img_not_implemented(self):
        self.disk_format.create_box_img("arbitrary")


class TestDiskFormatVagrantImplementation(TestDiskFormatVagrant):
    def setup(self):
        super(TestDiskFormatVagrantImplementation, self).setup()
        self.disk_format = DiskFormatVagrantgMock(
            self.xml_state, 'root_dir', 'target_dir',
            {'vagrantconfig': self.vagrantconfig}
        )

    def test_post_init_vagrant(self):
        assert self.disk_format.image_format == "vagrant.dummy.box"
        assert self.disk_format.provider == "dummy"

    @raises(KiwiFormatSetupError)
    def test_post_init_missing_custom_arguments(self):
        self.disk_format.post_init(custom_args=None)

    @raises(KiwiFormatSetupError)
    def test_post_init_missing_vagrantconfig(self):
        self.disk_format.post_init({'vagrantconfig': None})

    @patch('kiwi.defaults.Defaults.get_disk_format_types')
    @patch('kiwi.storage.subformat.vagrant_base.Command.run')
    @patch('kiwi.storage.subformat.vagrant_base.mkdtemp')
    @patch('kiwi.storage.subformat.vagrant_base.random.randrange')
    @patch_open
    def test_create_image_format(
        self, mock_open, mock_rand, mock_mkdtemp, mock_command,
        mock_get_disk_format_types
    ):
        # our dummy format will otherwise be rejected
        mock_get_disk_format_types.return_value = \
            [self.disk_format.image_format]

        mock_rand.return_value = 0xa
        mock_mkdtemp.return_value = 'tmpdir'
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
              "provider": "dummy"
            }
        ''').strip()
        vagrantfile = dedent('''
        Vagrant.configure("2") do |config|
          config.vm.base_mac = "00163E0A0A0A"
        end''').strip()

        self.disk_format.create_image_format()

        assert file_mock.write.call_args_list == [
            call(metadata_json), call(vagrantfile)
        ]

        box_file_name = 'target_dir/some-disk-image.x86_64-1.2.3.vagrant.dummy.box'

        assert mock_command.call_args_list == [
            call([
                'tar', '-C', 'tmpdir', '-czf', box_file_name,
                'metadata.json', 'Vagrantfile'
            ] + DiskFormatVagrantgMock.FILES
            )
        ]
