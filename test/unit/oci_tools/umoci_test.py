from mock import (
    Mock, patch, call
)

from kiwi.oci_tools.umoci import OCIUmoci


class TestOCIUmoci:
    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.oci_tools.base.datetime')
    @patch('kiwi.oci_tools.umoci.mkdtemp')
    def setup(self, mock_base_mkdtemp, mock_datetime, mock_cmd_caps):
        mock_base_mkdtemp.return_value = 'tmpdir'
        mock_cmd_caps.return_value = True
        strftime = Mock()
        strftime.strftime = Mock(return_value='current_date')
        mock_datetime.utcnow = Mock(
            return_value=strftime
        )
        self.oci = OCIUmoci()

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_init_container(self, mock_Command_run):
        self.oci.init_container()
        assert mock_Command_run.call_args_list == [
            call(['umoci', 'init', '--layout', 'tmpdir/oci_layout']),
            call(['umoci', 'new', '--image', 'tmpdir/oci_layout:base_layer'])
        ]

    @patch('kiwi.oci_tools.umoci.mkdtemp')
    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_unpack(self, mock_Command_run, mock_mkdtemp):
        mock_mkdtemp.return_value = 'oci_root'
        self.oci.unpack()
        mock_Command_run.assert_called_once_with(
            ['umoci', 'unpack', '--image', 'tmpdir/oci_layout:base_layer', 'oci_root']
        )

    @patch('kiwi.oci_tools.base.DataSync')
    def test_sync_rootfs(self, mock_sync):
        sync = Mock()
        mock_sync.return_value = sync
        self.oci.oci_root_dir = 'oci_root'
        self.oci.sync_rootfs('root_dir', exclude_list=['/dev', '/proc'])
        mock_sync.assert_called_once_with(
            'root_dir/', 'oci_root/rootfs'
        )
        sync.sync_data.assert_called_once_with(
            exclude=['/dev', '/proc'],
            options=[
                '-a', '-H', '-X', '-A', '--one-file-system',
                '--inplace', '--delete'
            ]
        )

    @patch('kiwi.oci_tools.base.DataSync')
    def test_import_rootfs(self, mock_sync):
        sync = Mock()
        mock_sync.return_value = sync
        self.oci.oci_root_dir = 'oci_root'
        self.oci.import_rootfs('root_dir', exclude_list=['/dev', '/proc'])
        mock_sync.assert_called_once_with(
            'oci_root/rootfs/', 'root_dir'
        )
        sync.sync_data.assert_called_once_with(
            exclude=['/dev', '/proc'],
            options=['-a', '-H', '-X', '-A', '--one-file-system', '--inplace']
        )

    @patch('kiwi.oci_tools.umoci.mkdtemp')
    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_repack(self, mock_Command_run, mock_mkdtemp):
        mock_mkdtemp.return_value = 'oci_root'
        oci_config = {
            'history': {
                'author': 'history author',
                'comment': 'This is a comment',
                'created_by': 'created by text'
            }
        }
        self.oci.unpack()
        self.oci.repack(oci_config)
        assert call(
            [
                'umoci', 'repack',
                '--history.comment=This is a comment',
                '--history.created_by=created by text',
                '--history.author=history author',
                '--history.created', 'current_date',
                '--image', 'tmpdir/oci_layout:base_layer', 'oci_root'
            ]
        ) in mock_Command_run.call_args_list

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_set_config(self, mock_Command_run):
        oci_config = {
            'container_tag': 'tag',
            'entry_command': ['/bin/bash', '-x'],
            'entry_subcommand': ['ls', '-l'],
            'maintainer': 'tux',
            'user': 'root',
            'workingdir': '/root',
            'expose_ports': ['80', '42'],
            'volumes': ['/var/log', '/tmp'],
            'environment': {'FOO': 'bar', 'PATH': '/bin'},
            'labels': {'a': 'value', 'b': 'value'},
        }
        self.oci.set_config(oci_config)
        mock_Command_run.assert_called_once_with(
            [
                'umoci', 'config', '--author=tux', '--config.user=root',
                '--config.workingdir=/root', '--config.entrypoint=/bin/bash',
                '--config.entrypoint=-x', '--config.cmd=ls', '--config.cmd=-l',
                '--config.volume=/var/log', '--config.volume=/tmp',
                '--config.exposedports=80', '--config.exposedports=42',
                '--config.env=FOO=bar', '--config.env=PATH=/bin',
                '--config.label=a=value', '--config.label=b=value',
                '--no-history', '--image', 'tmpdir/oci_layout:base_layer',
                '--tag', 'tag', '--created', 'current_date'
            ]
        )

    @patch('kiwi.oci_tools.umoci.mkdtemp')
    @patch('kiwi.oci_tools.base.datetime')
    @patch('kiwi.oci_tools.umoci.CommandCapabilities.has_option_in_help')
    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_set_config_with_history(
        self, mock_Command_run, mock_cmd_caps, mock_datetime, mock_mkdtemp
    ):
        oci_config = {
            'container_tag': 'tag',
            'entry_command': ['/bin/bash', '-x'],
            'entry_subcommand': ['ls', '-l'],
            'maintainer': 'tux',
            'user': 'root',
            'workingdir': '/root',
            'expose_ports': ['80', '42'],
            'volumes': ['/var/log', '/tmp'],
            'environment': {'FOO': 'bar', 'PATH': '/bin'},
            'labels': {'a': 'value', 'b': 'value'},
        }
        mock_mkdtemp.return_value = 'tmpdir'
        mock_cmd_caps.return_value = False
        strftime = Mock()
        strftime.strftime = Mock(return_value='current_date')
        mock_datetime.utcnow = Mock(
            return_value=strftime
        )
        oci = OCIUmoci()
        oci.set_config(oci_config)
        mock_Command_run.assert_called_once_with(
            [
                'umoci', 'config', '--author=tux', '--config.user=root',
                '--config.workingdir=/root', '--config.entrypoint=/bin/bash',
                '--config.entrypoint=-x', '--config.cmd=ls', '--config.cmd=-l',
                '--config.volume=/var/log', '--config.volume=/tmp',
                '--config.exposedports=80', '--config.exposedports=42',
                '--config.env=FOO=bar', '--config.env=PATH=/bin',
                '--config.label=a=value', '--config.label=b=value',
                '--image', 'tmpdir/oci_layout:base_layer',
                '--tag', 'tag', '--created', 'current_date'
            ]
        )

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_set_config_dervied_image(self, mock_Command_run):
        self.oci.set_config({'container_tag': 'tag'})
        mock_Command_run.assert_called_once_with([
            'umoci', 'config', '--no-history',
            '--image', 'tmpdir/oci_layout:base_layer', '--tag', 'tag',
            '--created', 'current_date'
        ])
        self.oci.working_image == 'tmpdir/oci_layout:tag'

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_set_config_clear_inherited_commands(
        self, mock_Command_run
    ):
        oci_config = {
            'container_tag': 'tag',
            'entry_command': [],
            'entry_subcommand': []
        }
        self.oci.set_config(oci_config)
        assert mock_Command_run.call_args_list == [
            call([
                'umoci', 'config', '--clear=config.entrypoint',
                '--clear=config.cmd', '--no-history',
                '--image', 'tmpdir/oci_layout:base_layer', '--tag', 'tag',
                '--created', 'current_date'
            ])
        ]

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_import_container_image(self, mock_Command_run):
        self.oci.import_container_image('oci-archive:image.tar')
        mock_Command_run.assert_called_once_with([
            'skopeo', 'copy', 'oci-archive:image.tar',
            'oci:tmpdir/oci_layout:base_layer'
        ])

    @patch('kiwi.oci_tools.umoci.Path.wipe')
    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_export_container_image(self, mock_Command_run, mock_wipe):
        self.oci.export_container_image(
            'image.tar', 'oci-archive', 'myimage:tag',
            ['myimage:tag2', 'myimage:tag3']
        )
        mock_Command_run.assert_called_once_with([
            'skopeo', 'copy', 'oci:tmpdir/oci_layout:base_layer',
            'oci-archive:image.tar:myimage:tag', '--additional-tag',
            'myimage:tag2', '--additional-tag', 'myimage:tag3'
        ])
        mock_wipe.assert_called_once_with('image.tar')

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_post_process(self, mock_Command_run):
        self.oci.post_process()
        mock_Command_run.assert_called_once_with(
            ['umoci', 'gc', '--layout', 'tmpdir/oci_layout']
        )

    @patch('kiwi.oci_tools.umoci.Path')
    def test_destructor(self, mock_Path):
        self.oci.oci_root_dir = 'oci_root'
        self.oci.__del__()
        assert mock_Path.wipe.call_args_list == [
            call('oci_root'), call('tmpdir')
        ]
