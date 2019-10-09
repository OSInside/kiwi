from mock import (
    patch, mock_open
)
from pytest import raises
import mock

from kiwi.exceptions import (
    KiwiTargetDirectoryNotFound,
    KiwiBootImageDumpError,
    KiwiConfigFileNotFound
)

from kiwi.boot.image.base import BootImageBase


class TestBootImageBase:
    @patch('kiwi.boot.image.base.os.path.exists')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_exists):
        mock_machine.return_value = 'x86_64'
        self.boot_xml_state = mock.Mock()
        self.xml_state = mock.Mock()
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='some-image'
        )
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.xml_state.build_type.get_boot = mock.Mock(
            return_value='oemboot/suse-13.2'
        )
        mock_exists.return_value = True
        self.boot_image = BootImageBase(
            self.xml_state, 'some-target-dir'
        )

    def test_boot_image_raises(self):
        with raises(KiwiTargetDirectoryNotFound):
            BootImageBase(
                self.xml_state, 'target-dir-does-not-exist', 'some-root-dir'
            )

    def test_prepare(self):
        with raises(NotImplementedError):
            self.boot_image.prepare()

    def test_create_initrd(self):
        with raises(NotImplementedError):
            self.boot_image.create_initrd()

    @patch('pickle.dump')
    def test_dump_error(self, mock_dump):
        mock_dump.side_effect = Exception
        with patch('builtins.open'):
            with raises(KiwiBootImageDumpError):
                self.boot_image.dump('filename')

    @patch('pickle.dump')
    @patch('kiwi.boot.image.base.BootImageBase.disable_cleanup')
    def test_dump(self, mock_disable_cleanup, mock_dump):
        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.boot_image.dump('filename')

        m_open.assert_called_once_with('filename', 'wb')
        mock_dump.assert_called_once_with(self.boot_image, m_open.return_value)
        mock_disable_cleanup.assert_called_once_with()

    def test_disable_cleanup(self):
        self.boot_image.disable_cleanup()
        assert self.boot_image.call_destructor is False

    def test_enable_cleanup(self):
        self.boot_image.enable_cleanup()
        assert self.boot_image.call_destructor is True

    @patch('os.listdir')
    def test_is_prepared(self, mock_listdir):
        mock_listdir.return_value = []
        assert self.boot_image.is_prepared() is False
        mock_listdir.return_value = ['a', 'b', 'c']
        assert self.boot_image.is_prepared() is True

    @patch('kiwi.boot.image.base.XMLState.copy_strip_sections')
    def test_import_system_description_elements(self, mock_strip):
        self.boot_image.import_system_description_elements()
        assert self.xml_state.copy_displayname.called
        assert self.xml_state.copy_name.called
        assert self.xml_state.copy_repository_sections.called
        assert self.xml_state.copy_drivers_sections.called
        assert mock_strip.called
        assert self.xml_state.copy_strip_sections.called
        assert self.xml_state.copy_preferences_subsections.called
        assert self.xml_state.copy_bootincluded_packages.called
        assert self.xml_state.copy_bootincluded_archives.called
        assert self.xml_state.copy_bootdelete_packages.called
        assert self.xml_state.copy_build_type_attributes.called
        assert self.xml_state.copy_systemdisk_section.called
        assert self.xml_state.copy_machine_section.called
        assert self.xml_state.copy_oemconfig_section.called

    def test_get_boot_description_directory(self):
        assert self.boot_image.get_boot_description_directory() == \
            '/usr/share/kiwi/custom_boot/oemboot/suse-13.2'

    @patch('kiwi.boot.image.base.BootImageBase.get_boot_description_directory')
    def test_load_boot_xml_description(self, mock_boot_dir):
        mock_boot_dir.return_value = None
        with raises(KiwiConfigFileNotFound):
            self.boot_image.load_boot_xml_description()

    def test_get_boot_names(self):
        with raises(NotImplementedError):
            self.boot_image.get_boot_names()

    def test_noop_methods(self):
        self.boot_image.include_module('module')
        self.boot_image.omit_module('module')
        self.boot_image.write_system_config_file({'config_key': 'value'})
