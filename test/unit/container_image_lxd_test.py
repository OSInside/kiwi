
import io
import tarfile
from mock import patch
from textwrap import dedent


import mock
import pytest

from .test_helper import *

from kiwi.exceptions import *
from kiwi.container.lxd import ContainerImageLxd

FAKE_ARCH = 'x86_64'
FAKE_UNIXTIME = 1466172644


class TestContainerImageLxd(object):
    def setup(self):
        self.lxd = ContainerImageLxd('root_dir')

    @patch('kiwi.container.lxd.lzma', new=True)
    @patch('kiwi.container.lxd.sys')
    def test_get_creation_method_py33plus_yes_lzma_yes_yields_newtype(
        self, mock_sys
    ):
        mock_sys.version_info = (3, 4, 1)
        self.lxd._create_new = mock.Mock()
        self.lxd._create_legacy = mock.Mock()
        self.lxd.create('filename')
        self.lxd._create_new.assert_called_once_with('filename')
        self.lxd._create_legacy.assert_not_called()

    @patch('kiwi.container.lxd.lzma', new=None)
    @patch('kiwi.container.lxd.sys')
    def test_get_creation_method_py33plus_yes_lzma_no_yields_legacytype(
        self, mock_sys
    ):
        mock_sys.version_info = (3, 4, 1)
        self.lxd._create_new = mock.Mock()
        self.lxd._create_legacy = mock.Mock()
        self.lxd.create('filename')
        self.lxd._create_new.assert_not_called()
        self.lxd._create_legacy.assert_called_once_with('filename')

    @patch('kiwi.container.lxd.lzma', new=True)
    @patch('kiwi.container.lxd.sys')
    def test_get_creation_method_py33plus_no_lzma_yes_yields_legacytype(
        self, mock_sys
    ):
        # I actually don't think this combination is seen in the wild,
        # but might as finish this for completeness sake.
        mock_sys.version_info = (3, 0)
        self.lxd._create_new = mock.Mock()
        self.lxd._create_legacy = mock.Mock()
        self.lxd.create('filename')
        self.lxd._create_new.assert_not_called()
        self.lxd._create_legacy.assert_called_once_with('filename')

    @patch('kiwi.container.lxd.lzma', new=None)
    @patch('kiwi.container.lxd.sys')
    def test_get_creation_method_py33plus_no_lzma_no_yields_legacytype(
        self, mock_sys
    ):
        mock_sys.version_info = (3, 0)
        self.lxd._create_new = mock.Mock()
        self.lxd._create_legacy = mock.Mock()
        self.lxd.create('filename')
        self.lxd._create_new.assert_not_called()
        self.lxd._create_legacy.assert_called_once_with('filename')

    @patch('kiwi.container.lxd.time.time')
    @patch('kiwi.container.lxd.platform.machine')
    @patch('kiwi.container.lxd.os.path.exists')
    @patch('kiwi.container.lxd.io.open')
    def test_get_metadata_yaml_with_user_data_existing(
        self, mock_open, mock_exists, mock_machine, mock_time
    ):
        mock_exists.return_value = True
        mock_machine.return_value = FAKE_ARCH
        mock_time.return_value = FAKE_UNIXTIME
        # open/file/read test doubling is a bit painful, apologies...
        # TODO: perhaps use something like testfixtures.TempDirectory
        mock_file = mock.Mock()
        mock_file.read.return_value = dedent(u"""\
            fakevar1: fakeval1
            fakevar2: fakeval2
            """)
        mock_context_manager = mock.MagicMock(spec=io.TextIOBase)
        mock_context_manager.__enter__.return_value = mock_file
        mock_open.return_value = mock_context_manager

        expected = dedent(u"""\
            # auto-populated by kiwi
            architecture: {arch}
            creation_date: {unixtime}
            # back to user content...
            fakevar1: fakeval1
            fakevar2: fakeval2
            """.format(arch=FAKE_ARCH, unixtime=FAKE_UNIXTIME))
        actual = self.lxd._get_metadata_yaml()
        assert expected == actual

    @patch('kiwi.container.lxd.time.time')
    @patch('kiwi.container.lxd.platform.machine')
    @patch('kiwi.container.lxd.os.path.exists')
    @patch('kiwi.container.lxd.io.open')
    @raises(ValueError)
    def test_get_metadata_yaml_with_conflicting_user_data_existing(
        self, mock_open, mock_exists, mock_machine, mock_time
    ):
        mock_exists.return_value = True
        mock_machine.return_value = FAKE_ARCH
        mock_time.return_value = FAKE_UNIXTIME
        # open/file/read test doubling is a bit painful, apologies...
        # TODO: perhaps use something like testfixtures.TempDirectory
        mock_file = mock.Mock()
        mock_file.read.return_value = dedent(u"""\
            architecture: 6502
            fakevar1: fakeval1
            fakevar2: fakeval2
            """)
        mock_context_manager = mock.MagicMock(spec=io.TextIOBase)
        mock_context_manager.__enter__.return_value = mock_file
        mock_open.return_value = mock_context_manager
        self.lxd._get_metadata_yaml()

    @patch('kiwi.container.lxd.time.time')
    @patch('kiwi.container.lxd.platform.machine')
    @patch('kiwi.container.lxd.os.path.exists')
    def test_get_metadata_yaml_without_user_data_existing(
        self, mock_exists, mock_machine, mock_time
    ):
        mock_exists.return_value = False
        mock_machine.return_value = FAKE_ARCH
        mock_time.return_value = FAKE_UNIXTIME
        expected = dedent(u"""\
            # auto-populated by kiwi
            architecture: {arch}
            creation_date: {unixtime}
            # back to user content...
            """.format(arch=FAKE_ARCH, unixtime=FAKE_UNIXTIME))
        actual = self.lxd._get_metadata_yaml()

    def test_get_compression_type_plaintar(self):
        compression_type = self.lxd._get_compression_type(filename='foo.tar')
        assert compression_type == ''

    def test_get_compression_type_gz(self):
        compression_type = self.lxd._get_compression_type(filename='foo.tar.gz')
        assert compression_type == ':gz'

    def test_get_compression_type_bz2(self):
        compression_type = self.lxd._get_compression_type(filename='foo.tar.bz2')
        assert compression_type == ':bz2'

    def test_get_compression_type_xz(self):
        compression_type = self.lxd._get_compression_type(filename='foo.tar.xz')
        assert compression_type == ':xz'

    @raises(ValueError)
    def test_get_compression_type_unknown(self):
        self.lxd._get_compression_type(filename='foo.err')

    @patch('kiwi.container.lxd.time.time')
    @patch('kiwi.container.lxd.platform.machine')
    def test_create_new_with_user_metadata(self, mock_machine, mock_time, tmpdir):
        mock_machine.return_value = FAKE_ARCH
        mock_time.return_value = FAKE_UNIXTIME
        # tmpdir+src will be root_dir
        vpath_src = tmpdir.mkdir('src')
        vpath_src_image = vpath_src.mkdir('image')
        vpath_src_fakefile = vpath_src.join('fakefile.txt').write('hi\n')
        vpath_src_metadata = vpath_src_image.mkdir('lxd_metadata')
        vpath_src_metadata_yaml = vpath_src_metadata.join('metadata.yaml')
        vpath_src_metadata_yaml.write(dedent(u"""\
            fakevar1: fakeval1
            fakevar2: fakeval2
            """))
        vpath_src_metadata_templates = vpath_src_metadata.mkdir('templates')
        vpath_src_metadata_templates_fakefile = vpath_src_metadata_templates.join(
            'fakefile.txt')
        vpath_src_metadata_templates_fakefile.write(u"yo\n")
        self.lxd.root_dir = str(vpath_src)
        # tmpdir+dst will be output (image) dir
        vpath_dst = tmpdir.mkdir('dst')
        # NB: don't use .xz (since py27 doesn't support lzma)
        vpath_artifact = vpath_dst.join('lxd_artifact.tar.gz')
        path_artifact = str(vpath_artifact)
        self.lxd._create_new(path_artifact)
        with tarfile.open(path_artifact) as tf:
            # firstly, verify the archive members
            expected = [
                'metadata.yaml',
                'rootfs',
                'rootfs/fakefile.txt',
                'templates',
                'templates/fakefile.txt',
            ]
            actual = sorted(tf.getnames())
            assert expected == actual
            # secondly, verify the content
            expected = dedent(u"""\
                # auto-populated by kiwi
                architecture: {arch}
                creation_date: {unixtime}
                # back to user content...
                fakevar1: fakeval1
                fakevar2: fakeval2
                """.format(arch=FAKE_ARCH, unixtime=FAKE_UNIXTIME)).encode('utf-8')
            actual = tf.extractfile('metadata.yaml').read()
            assert expected == actual
            assert u'hi\n'.encode('utf-8') == tf.extractfile('rootfs/fakefile.txt').read()
            assert u'yo\n'.encode('utf-8') == tf.extractfile('templates/fakefile.txt').read()

    @patch('kiwi.container.lxd.time.time')
    @patch('kiwi.container.lxd.platform.machine')
    def test_create_new_without_user_metadata(self, mock_machine, mock_time, tmpdir):
        mock_machine.return_value = FAKE_ARCH
        mock_time.return_value = FAKE_UNIXTIME
        # tmpdir+src will be root_dir
        vpath_src = tmpdir.mkdir('src')
        vpath_src_image = vpath_src.mkdir('image')
        vpath_src_fakefile = vpath_src.join('fakefile.txt').write('hi\n')
        self.lxd.root_dir = str(vpath_src)
        # tmpdir+dst will be output (image) dir
        vpath_dst = tmpdir.mkdir('dst')
        # NB: don't use .xz (since py27 doesn't support lzma)
        vpath_artifact = vpath_dst.join('lxd_artifact.tar')
        path_artifact = str(vpath_artifact)
        self.lxd._create_new(path_artifact)
        with tarfile.open(path_artifact) as tf:
            # firstly, verify the archive members
            expected = [
                'metadata.yaml',
                'rootfs',
                'rootfs/fakefile.txt',
            ]
            actual = sorted(tf.getnames())
            assert expected == actual
            # secondly, verify the content
            expected = dedent(u"""\
                # auto-populated by kiwi
                architecture: {arch}
                creation_date: {unixtime}
                # back to user content...
                """.format(arch=FAKE_ARCH, unixtime=FAKE_UNIXTIME)).encode('utf-8')
            actual = tf.extractfile('metadata.yaml').read()
            assert expected == actual
            assert u'hi\n'.encode('utf-8') == tf.extractfile('rootfs/fakefile.txt').read()

    @patch('kiwi.container.lxd.time.time')
    @patch('kiwi.container.lxd.platform.machine')
    def test_create_legacy_with_user_metadata(self, mock_machine, mock_time, tmpdir):
        mock_machine.return_value = FAKE_ARCH
        mock_time.return_value = FAKE_UNIXTIME
        # tmpdir+src will be root_dir
        vpath_src = tmpdir.mkdir('src')
        vpath_src_image = vpath_src.mkdir('image')
        vpath_src_fakefile = vpath_src.join('fakefile.txt').write('hi\n')
        vpath_src_metadata = vpath_src_image.mkdir('lxd_metadata')
        vpath_src_metadata_yaml = vpath_src_metadata.join('metadata.yaml')
        vpath_src_metadata_yaml.write(dedent(u"""\
            fakevar1: fakeval1
            fakevar2: fakeval2
            """))
        vpath_src_metadata_templates = vpath_src_metadata.mkdir('templates')
        vpath_src_metadata_templates_fakefile = vpath_src_metadata_templates.join(
            'fakefile.txt')
        vpath_src_metadata_templates_fakefile.write(u"yo\n")
        self.lxd.root_dir = str(vpath_src)
        # tmpdir+dst will be output (image) dir
        vpath_dst = tmpdir.mkdir('dst')
        # NB: don't use .xz (since py27 doesn't support lzma)
        vpath_artifact = vpath_dst.join('lxd_artifact.tar.gz')
        path_artifact = str(vpath_artifact)
        self.lxd._create_legacy(path_artifact)
        with tarfile.open(path_artifact) as tf:
            # firstly, verify the archive members
            expected = [
                'metadata.yaml',
                'rootfs',
                'rootfs/fakefile.txt',
                'templates',
                'templates/fakefile.txt',
                ]
            actual = sorted(tf.getnames())
            assert expected == actual
            # secondly, verify the content
            expected = dedent(u"""\
                # auto-populated by kiwi
                architecture: {arch}
                creation_date: {unixtime}
                # back to user content...
                fakevar1: fakeval1
                fakevar2: fakeval2
                """.format(arch=FAKE_ARCH, unixtime=FAKE_UNIXTIME)).encode('utf-8')
            actual = tf.extractfile('metadata.yaml').read()
            assert expected == actual
            assert u'hi\n'.encode('utf-8') == tf.extractfile('rootfs/fakefile.txt').read()
            assert u'yo\n'.encode('utf-8') == tf.extractfile('templates/fakefile.txt').read()

    @patch('kiwi.container.lxd.time.time')
    @patch('kiwi.container.lxd.platform.machine')
    def test_create_legacy_without_user_metadata(self, mock_machine, mock_time, tmpdir):
        mock_machine.return_value = FAKE_ARCH
        mock_time.return_value = FAKE_UNIXTIME
        # tmpdir+src will be root_dir
        vpath_src = tmpdir.mkdir('src')
        vpath_src_image = vpath_src.mkdir('image')
        vpath_src_fakefile = vpath_src.join('fakefile.txt').write('hi\n')
        self.lxd.root_dir = str(vpath_src)
        # tmpdir+dst will be output (image) dir
        vpath_dst = tmpdir.mkdir('dst')
        # NB: don't use .xz (since py27 doesn't support lzma)
        vpath_artifact = vpath_dst.join('lxd_artifact.tar.gz')
        path_artifact = str(vpath_artifact)
        self.lxd._create_legacy(path_artifact)
        with tarfile.open(path_artifact) as tf:
            # firstly, verify the archive members
            expected = [
                'metadata.yaml',
                'rootfs',
                'rootfs/fakefile.txt',
                ]
            actual = sorted(tf.getnames())
            assert expected == actual
            # secondly, verify the content
            expected = dedent(u"""\
                # auto-populated by kiwi
                architecture: {arch}
                creation_date: {unixtime}
                # back to user content...
                """.format(arch=FAKE_ARCH, unixtime=FAKE_UNIXTIME)).encode('utf-8')
            actual = tf.extractfile('metadata.yaml').read()
            assert expected == actual
            assert u'hi\n'.encode('utf-8') == tf.extractfile('rootfs/fakefile.txt').read()
