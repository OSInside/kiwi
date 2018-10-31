from mock import (
    Mock, patch, call
)

from kiwi.oci_tools.umoci import OCIUmoci


class TestOCIBase(object):
    @patch('kiwi.oci_tools.base.mkdtemp')
    def setup(self, mock_mkdtemp):
        mock_mkdtemp.return_value = 'tmpdir'
        self.oci = OCIUmoci('tag')

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_init_layout(self, mock_Command_run):
        self.oci.init_layout()
        assert mock_Command_run.call_args_list == [
            call(['umoci', 'init', '--layout', 'tmpdir/oci_layout']),
            call(['umoci', 'new', '--image', 'tmpdir/oci_layout:tag'])
        ]

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_init_layout_base_image(self, mock_Command_run):
        self.oci.init_layout(True)
        mock_Command_run.assert_called_once_with(
            [
                'umoci', 'config', '--image',
                'tmpdir/oci_layout:base_layer', '--tag', 'tag'
            ]
        )

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_unpack(self, mock_Command_run):
        self.oci.unpack('dir')
        mock_Command_run.assert_called_once_with(
            ['umoci', 'unpack', '--image', 'tmpdir/oci_layout:tag', 'dir']
        )

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_repack(self, mock_Command_run):
        self.oci.repack('dir')
        mock_Command_run.assert_called_once_with(
            ['umoci', 'repack', '--image', 'tmpdir/oci_layout:tag', 'dir']
        )

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_add_tag(self, mock_Command_run):
        self.oci.add_tag('other_tag')
        mock_Command_run.assert_called_once_with(
            [
                'umoci', 'config', '--image', 'tmpdir/oci_layout:tag',
                '--tag', 'other_tag'
            ]
        )

    @patch('kiwi.oci_tools.umoci.Command.run')
    @patch('kiwi.oci_tools.umoci.datetime')
    def test_set_config(self, mock_datetime, mock_Command_run):
        strftime = Mock()
        strftime.strftime = Mock(return_value='current_date')
        mock_datetime.utcnow = Mock(
            return_value=strftime
        )
        oci_config = {
            'entry_command': ['/bin/bash', '-x'],
            'entry_subcommand': ['ls', '-l'],
            'maintainer': 'tux',
            'user': 'root',
            'workingdir': '/root',
            'expose_ports': ['80', '42'],
            'volumes': ['/var/log', '/tmp'],
            'environment': {'PATH': '/bin', 'FOO': 'bar'},
            'labels': {'a': 'value', 'b': 'value'}
        }
        self.oci.set_config(oci_config)
        mock_Command_run.assert_called_once_with(
            [
                'umoci', 'config', '--author=tux', '--config.user=root',
                '--config.workingdir=/root', '--config.entrypoint=/bin/bash',
                '--config.entrypoint=-x', '--config.cmd=ls', '--config.cmd=-l',
                '--config.volume=/var/log', '--config.volume=/tmp',
                '--config.exposedports=80', '--config.exposedports=42',
                '--config.env=PATH=/bin', '--config.env=FOO=bar',
                '--config.label=a=value', '--config.label=b=value',
                '--image', 'tmpdir/oci_layout:tag', '--created', 'current_date'
            ]
        )

    @patch('kiwi.oci_tools.umoci.Command.run')
    @patch('kiwi.oci_tools.umoci.datetime')
    def test_set_config_clear_inherited_commands(
        self, mock_datetime, mock_Command_run
    ):
        strftime = Mock()
        strftime.strftime = Mock(return_value='current_date')
        mock_datetime.utcnow = Mock(
            return_value=strftime
        )
        oci_config = {
            'entry_command': [],
            'entry_subcommand': []
        }
        self.oci.set_config(oci_config)
        mock_Command_run.assert_called_once_with(
            [
                'umoci', 'config', '--clear=config.entrypoint',
                '--clear=config.cmd', '--image', 'tmpdir/oci_layout:tag',
                '--created', 'current_date'
            ]
        )

    @patch('kiwi.oci_tools.umoci.Command.run')
    def test_garbage_collect(self, mock_Command_run):
        self.oci.garbage_collect()
        mock_Command_run.assert_called_once_with(
            ['umoci', 'gc', '--layout', 'tmpdir/oci_layout']
        )
