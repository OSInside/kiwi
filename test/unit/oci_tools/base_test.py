from pytest import raises

from kiwi.oci_tools.base import OCIBase


class TestOCIBase:
    def setup(self):
        self.oci = OCIBase()

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
