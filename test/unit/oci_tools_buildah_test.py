from mock import (
    Mock, patch, call
)
from pytest import raises
from collections import namedtuple

from kiwi.oci_tools.buildah import OCIBuildah
from kiwi.exceptions import KiwiBuildahError


class TestOCIBuildah(object):
    @patch('kiwi.oci_tools.base.datetime')
    def setup(self, mock_datetime):
        strftime = Mock()
        strftime.strftime = Mock(return_value='current_date')
        mock_datetime.utcnow = Mock(
            return_value=strftime
        )
        self.oci = OCIBuildah()

    @patch('kiwi.oci_tools.umoci.Command.run')
    def teardown(self, mock_cmd_run):
        del self.oci
        mock_cmd_run.reset_mock()

    @patch('kiwi.oci_tools.buildah.random.choice')
    @patch('kiwi.oci_tools.buildah.Command.run')
    def test_init_container(self, mock_Command_run, mock_choice):
        mock_choice.return_value = 'x'
        self.oci.init_container()
        mock_Command_run.assert_called_once_with(
            ['buildah', 'from', '--name', 'kiwi-container-xxxxxx', 'scratch']
        )

    def test_init_container_fail(self):
        with raises(KiwiBuildahError):
            self.oci.working_container = 'initialized'
            self.oci.init_container()

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_unpack(self, mock_cmd_run):
        command_type = namedtuple('command', ['output'])
        mock_cmd_run.return_value = command_type(output='mountpoint-dir')
        self.oci.working_container = 'kiwi-working'
        self.oci.unpack()
        mock_cmd_run.assert_called_once_with(
            ['buildah', 'mount', 'kiwi-working']
        )
        assert self.oci.oci_root_dir == 'mountpoint-dir'

    @patch('kiwi.oci_tools.base.DataSync')
    def test_sync_rootfs(self, mock_sync):
        sync = Mock()
        mock_sync.return_value = sync
        self.oci.oci_root_dir = 'oci_root'
        self.oci.sync_rootfs('root_dir', exclude_list=['/dev', '/proc'])
        mock_sync.assert_called_once_with(
            'root_dir/', 'oci_root'
        )
        sync.sync_data.assert_called_once_with(
            exclude=['/dev', '/proc'],
            options=['-a', '-H', '-X', '-A', '--delete']
        )

    @patch('kiwi.oci_tools.base.DataSync')
    def test_import_rootfs(self, mock_sync):
        sync = Mock()
        mock_sync.return_value = sync
        self.oci.oci_root_dir = 'oci_root'
        self.oci.import_rootfs('root_dir', exclude_list=['/dev', '/proc'])
        mock_sync.assert_called_once_with(
            'oci_root/', 'root_dir'
        )
        sync.sync_data.assert_called_once_with(
            exclude=['/dev', '/proc'],
            options=['-a', '-H', '-X', '-A']
        )

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_repack(self, mock_cmd_run):
        self.oci.working_container = 'kiwi-working'
        self.oci.repack({})
        mock_cmd_run.assert_called_once_with(
            ['buildah', 'umount', 'kiwi-working']
        )

    @patch('kiwi.logger.log.warning')
    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_set_config(self, mock_cmd_run, mock_warn):
        oci_config = {
            'entry_command': ['/bin/bash', '-x'],
            'entry_subcommand': ['ls', '-l'],
            'maintainer': 'tux',
            'user': 'root',
            'workingdir': '/root',
            'expose_ports': ['80', '42'],
            'volumes': ['/var/log', '/tmp'],
            'environment': {'FOO': 'bar', 'PATH': '/bin'},
            'labels': {'a': 'value', 'b': 'value'},
            'history': {
                'author': 'history author',
                'comment': 'This is a comment',
                'created_by': 'created by text'
            }
        }
        self.oci.working_container = 'kiwi-working'
        self.oci.set_config(oci_config)
        mock_cmd_run.assert_called_once_with([
            'buildah', 'config', '--author=tux', '--user=root',
            '--workingdir=/root', '--entrypoint=["/bin/bash","-x"]',
            '--cmd=ls -l',
            '--volume=/var/log', '--volume=/tmp', '--port=80', '--port=42',
            '--env=FOO=bar', '--env=PATH=/bin', '--label=a=value',
            '--label=b=value', '--history-comment=This is a comment',
            '--created-by=created by text', 'kiwi-working'
        ])
        assert mock_warn.called

    @patch('kiwi.oci_tools.buildah.random.choice')
    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_post_process(self, mock_cmd_run, mock_choice):
        mock_choice.return_value = 'x'
        self.oci.working_container = 'kiwi-container'
        self.oci.post_process()
        mock_cmd_run.assert_called_once_with([
            'buildah', 'commit', '--rm', '--format', 'oci',
            'kiwi-container', 'kiwi-image-xxxxxx:tag-xxxxxx'
        ])

    def test_post_processi_fail(self):
        with raises(KiwiBuildahError):
            self.oci.working_container = None
            self.oci.post_process()

    @patch('kiwi.oci_tools.buildah.random.choice')
    @patch('kiwi.oci_tools.buildah.Command.run')
    def test_import_container_image(self, mock_Command_run, mock_choice):
        mock_choice.return_value = 'x'
        self.oci.import_container_image('oci-archive:image.tar')
        assert mock_Command_run.call_args_list == [
            call([
                'skopeo', 'copy', 'oci-archive:image.tar',
                'containers-storage:kiwi-image-xxxxxx:base_layer'
            ]),
            call([
                'buildah', 'from', '--name', 'kiwi-container-xxxxxx',
                'containers-storage:kiwi-image-xxxxxx:base_layer'
            ])
        ]

    @patch('kiwi.oci_tools.buildah.random.choice')
    @patch('kiwi.oci_tools.buildah.Command.run')
    def test_import_container_image_fail_create_container(
        self, mock_Command_run, mock_choice
    ):
        with raises(KiwiBuildahError):
            mock_choice.return_value = 'x'
            self.oci.working_container = 'initialized'
            self.oci.import_container_image('oci-archive:image.tar')
            mock_Command_run.assert_called_once_with(
                [
                    'skopeo', 'copy', 'oci-archive:image.tar',
                    'containers-storage:kiwi-image-xxxxxx:base_layer'
                ]
            )

    def test_import_container_image_fail_load_image(self):
        with raises(KiwiBuildahError):
            self.oci.imported_image = 'initialized'
            self.oci.import_container_image('oci-archive:image.tar')

    @patch('kiwi.oci_tools.buildah.Path.wipe')
    @patch('kiwi.oci_tools.buildah.Command.run')
    def test_export_container_image(self, mock_Command_run, mock_wipe):
        self.oci.working_image = 'kiwi-image:tag'
        self.oci.export_container_image(
            'image.tar', 'docker-archive', 'myimage:tag',
            ['myimage:tag2', 'myimage:tag3']
        )
        mock_Command_run.assert_called_once_with([
            'skopeo', 'copy', 'containers-storage:kiwi-image:tag',
            'docker-archive:image.tar:myimage:tag', '--additional-tag',
            'myimage:tag2', '--additional-tag', 'myimage:tag3'
        ])
        mock_wipe.assert_called_once_with('image.tar')

    @patch('kiwi.oci_tools.buildah.Path.wipe')
    @patch('kiwi.oci_tools.buildah.Command.run')
    def test_export_container_image_imported(self, mock_Command_run, mock_wipe):
        self.oci.working_image = None
        self.oci.imported_image = 'kiwi-image:base_layer'
        self.oci.export_container_image(
            'image.tar', 'docker-archive', 'myimage:tag',
            ['myimage:tag2', 'myimage:tag3']
        )
        mock_Command_run.assert_called_once_with([
            'skopeo', 'copy', 'containers-storage:kiwi-image:base_layer',
            'docker-archive:image.tar:myimage:tag', '--additional-tag',
            'myimage:tag2', '--additional-tag', 'myimage:tag3'
        ])
        mock_wipe.assert_called_once_with('image.tar')

    @patch('kiwi.oci_tools.buildah.Path.wipe')
    @patch('kiwi.oci_tools.buildah.Command.run')
    def test_export_container_image_fail(self, mock_Command_run, mock_wipe):
        with raises(KiwiBuildahError):
            self.oci.working_image = None
            self.oci.imported_image = None
            self.oci.export_container_image(
                'image.tar', 'docker-archive', 'myimage:tag',
                ['myimage:tag2', 'myimage:tag3']
            )
            mock_wipe.assert_called_once_with('image.tar')
