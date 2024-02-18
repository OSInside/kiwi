from pytest import raises
from unittest.mock import patch

from kiwi.oci_tools.base import OCIBase


class TestOCIBase:
    def setup(self):
        self.oci = OCIBase()

    def setup_method(self, cls):
        self.setup()

    def test_init_container(self):
        with raises(NotImplementedError):
            self.oci.init_container()

    def test_import_container_image(self):
        with raises(NotImplementedError):
            self.oci.import_container_image('oci-archive:image.xz')

    def test_export_container_image(self):
        with raises(NotImplementedError):
            self.oci.export_container_image(
                'image.xz', 'docker-archive', 'myimage:tag'
            )

    def test_unpack(self):
        with raises(NotImplementedError):
            self.oci.unpack()

    def test_sync_rootfs(self):
        with raises(NotImplementedError):
            self.oci.sync_rootfs('root_dir')

    def test_import_rootfs(self):
        with raises(NotImplementedError):
            self.oci.import_rootfs('root_dir')

    def test_repack(self):
        with raises(NotImplementedError):
            self.oci.repack({})

    def test_set_config(self):
        with raises(NotImplementedError):
            self.oci.set_config({})

    def test_post_process(self):
        with raises(NotImplementedError):
            self.oci.post_process()

    @patch('kiwi.oci_tools.base.Path.which')
    @patch('kiwi.oci_tools.base.CommandCapabilities.check_version')
    def test_skopeo_provides_tmpdir_option(
        self, mock_Path_which, mock_CommandCapabilities_check_version
    ):
        mock_Path_which.return_value = 'skopeo'
        mock_CommandCapabilities_check_version.return_value = (0, 2, 0)
        assert self.oci._skopeo_provides_tmpdir_option() is True
        mock_Path_which.return_value = None
        assert self.oci._skopeo_provides_tmpdir_option() is False
