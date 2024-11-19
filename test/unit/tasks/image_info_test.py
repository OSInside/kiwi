import sys

from unittest.mock import (
    patch, call, Mock, MagicMock
)

import kiwi

from ..test_helper import argv_kiwi_tests

from kiwi.tasks.image_info import ImageInfoTask

from collections import (
    namedtuple, OrderedDict
)


class TestImageInfoTask:
    def setup(self):
        sys.argv = [
            sys.argv[0], 'image', 'info',
            '--description', '../data/image_info',
            '--resolve-package-list'
        ]
        result_type = namedtuple(
            'result_type', [
                'uri', 'installsize_bytes', 'arch', 'version', 'checksum'
            ]
        )
        self.result_info = {
            'image': 'LimeJeOS',
            'resolved-packages': {
                'packagename': {
                    'version': '0.8.15', 'arch': 'x86_64',
                    'source': 'uri', 'status': 'added_by_dependency_solver',
                    'installsize_bytes': 42
                },
                'filesystem': {
                    'version': '42', 'arch': 'x86_64',
                    'source': 'uri', 'status': 'listed_in_kiwi_description',
                    'installsize_bytes': 0
                }
            }
        }
        self.runtime_checker = Mock()
        kiwi.tasks.base.RuntimeChecker = Mock(
            return_value=self.runtime_checker
        )
        self.runtime_config = Mock()
        kiwi.tasks.base.RuntimeConfig = Mock(
            return_value=self.runtime_config
        )
        self.solver = MagicMock()
        self.solver.solve = Mock(
            return_value={
                'packagename': result_type(
                    uri='uri', installsize_bytes=42,
                    arch='x86_64', version='0.8.15', checksum='checksum'
                ),
                'filesystem': result_type(
                    uri='uri', installsize_bytes=0,
                    arch='x86_64', version='42', checksum='checksum'
                )
            }
        )
        kiwi.tasks.image_info.Sat = Mock(
            return_value=self.solver
        )

        self.solver_repository = Mock()
        kiwi.tasks.image_info.SolverRepository = Mock(
            return_value=self.solver_repository
        )

        kiwi.tasks.image_info.Help = Mock(
            return_value=Mock()
        )
        self.task = ImageInfoTask()

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['info'] = False
        self.task.command_args['--description'] = '../data/image_info'
        self.task.command_args['--add-repo'] = []
        self.task.command_args['--ignore-repos'] = False
        self.task.command_args['--resolve-package-list'] = False
        self.task.command_args['--list-profiles'] = False
        self.task.command_args['--print-kiwi-env'] = False
        self.task.command_args['--print-xml'] = False
        self.task.command_args['--print-yaml'] = False
        self.task.command_args['--print-toml'] = False

    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info(self, mock_out):
        self._init_command_args()
        self.task.command_args['info'] = True
        self.task.process()
        self.runtime_checker.check_repositories_configured.assert_called_once_with()
        mock_out.assert_called_once_with(
            {'image': 'LimeJeOS'}
        )

    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info_color_output(self, mock_out):
        self._init_command_args()
        self.task.command_args['info'] = True
        self.task.global_args['--color-output'] = True
        self.task.process()
        mock_out.assert_called_once_with(
            {'image': 'LimeJeOS'}, style='color'
        )

    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info_list_profiles(self, mock_out):
        self._init_command_args()
        self.task.command_args['info'] = True
        self.task.command_args['--list-profiles'] = True
        self.task.process()
        self.runtime_checker.check_repositories_configured.assert_called_once_with()
        mock_out.assert_called_once_with(
            {'image': 'LimeJeOS', 'profile_names': ['some']}
        )

    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info_print_kiwi_env(self, mock_out):
        self._init_command_args()
        self.task.command_args['info'] = True
        self.task.command_args['--print-kiwi-env'] = True
        self.task.process()
        self.runtime_checker.check_repositories_configured.assert_called_once_with()

        mock_out.assert_called_once_with(
            {
                'image': 'LimeJeOS',
                'kiwi_env': OrderedDict(
                    [
                        ('kiwi_align', '1048576'),
                        ('kiwi_boot_timeout', ''),
                        ('kiwi_bootkernel', ''),
                        ('kiwi_bootloader', 'grub2'),
                        ('kiwi_bootloader_console', 'default:default'),
                        ('kiwi_bootprofile', ''),
                        ('kiwi_btrfs_root_is_snapshot', ''),
                        ('kiwi_cmdline', ''),
                        ('kiwi_compressed', ''),
                        ('kiwi_delete', ''),
                        ('kiwi_devicepersistency', ''),
                        ('kiwi_displayname', 'Bob'),
                        ('kiwi_drivers', ''),
                        ('kiwi_firmware', ''),
                        ('kiwi_fsmountoptions', ''),
                        ('kiwi_gpt_hybrid_mbr', ''),
                        ('kiwi_hybridpersistent', ''),
                        ('kiwi_hybridpersistent_filesystem', ''),
                        ('kiwi_iname', 'LimeJeOS'),
                        ('kiwi_initrd_system', 'dracut'),
                        ('kiwi_installboot', ''),
                        ('kiwi_iversion', '1.13.2'),
                        ('kiwi_keytable', 'us.map.gz'),
                        ('kiwi_language', 'en_US'),
                        ('kiwi_live_volid', 'CDROM'),
                        ('kiwi_loader_theme', 'openSUSE'),
                        ('kiwi_luks_empty_passphrase', 'false'),
                        ('kiwi_profiles', ''),
                        ('kiwi_ramonly', ''),
                        ('kiwi_revision', '$Format:%H$'),
                        ('kiwi_rootpartuuid', ''),
                        ('kiwi_sectorsize', '512'),
                        ('kiwi_showlicense', ''),
                        ('kiwi_splash_theme', 'openSUSE'),
                        ('kiwi_startsector', '2048'),
                        ('kiwi_strip_delete', ''),
                        ('kiwi_strip_libs', ''),
                        ('kiwi_strip_tools', ''),
                        ('kiwi_target_blocksize', ''),
                        ('kiwi_target_removable', ''),
                        ('kiwi_timezone', 'Europe/Berlin'),
                        ('kiwi_type', 'iso'),
                        ('kiwi_vga', ''),
                        ('kiwi_wwid_wait_timeout', '')
                    ]
                )
            }
        )

    @patch('kiwi.tasks.image_info.DataOutput')
    @patch('kiwi.tasks.image_info.SolverRepository.new')
    @patch('kiwi.tasks.image_info.Uri')
    @patch('kiwi.tasks.image_info.SolverRepositoryBase.get_repo_type')
    def test_process_image_info_resolve_package_list(
        self, mock_get_repo_type, mock_uri, mock_solver_repo_new, mock_out
    ):
        uri = Mock()
        uri.uri = 'http://example.org/some/path'
        mock_uri.return_value = uri
        mock_get_repo_type.return_value = 'apt-deb'
        self.solver.set_dist_type.return_value = {
            'arch': 'amd64'
        }
        self._init_command_args()
        self.task.command_args['info'] = True
        self.task.command_args['--resolve-package-list'] = True
        self.task.process()

        assert self.solver.add_repository.called
        assert mock_uri.call_args_list == [
            call(uri='http://us.archive.ubuntu.com/ubuntu/', source_type=''),
            call(
                'http://us.archive.ubuntu.com/ubuntu/dists/focal/'
                'main/binary-amd64', 'apt-deb', ''
            ),
            call(
                'http://us.archive.ubuntu.com/ubuntu/dists/focal/'
                'multiverse/binary-amd64', 'apt-deb', ''
            ),
            call(
                'http://us.archive.ubuntu.com/ubuntu/dists/focal/'
                'restricted/binary-amd64', 'apt-deb', ''
            ),
            call(
                'http://us.archive.ubuntu.com/ubuntu/dists/focal/'
                'universe/binary-amd64', 'apt-deb', ''
            ),
            call('obs://Devel:PubCloud:AmazonEC2/SLE_12_GA', 'rpm-md', '')
        ]
        mock_out.assert_called_once_with(self.result_info)

    @patch('kiwi.xml_state.XMLState.add_repository')
    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info_add_repo(self, mock_out, mock_state):
        self._init_command_args()
        self.task.command_args['--add-repo'] = [
            'http://example.com,rpm-md,alias'
        ]
        self.task.process()
        mock_state.assert_called_once_with(
            'http://example.com', 'rpm-md', 'alias', None
        )

    @patch('kiwi.xml_state.XMLState.delete_repository_sections')
    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info_delete_repos(self, mock_out, mock_delete_repos):
        self._init_command_args()
        self.task.command_args['--ignore-repos'] = True
        self.task.process()
        mock_delete_repos.assert_called_once_with()

    def test_process_image_info_help(self):
        self._init_command_args()
        self.task.command_args['help'] = True
        self.task.command_args['info'] = True
        self.task.process()
        self.task.manual.show.assert_called_once_with(
            'kiwi::image::info'
        )

    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info_print_xml(self, mock_out):
        self._init_command_args()
        self.task.command_args['--print-xml'] = True
        self.task.process()
        tmpfile, message = mock_out.display_file.call_args.args
        assert tmpfile.startswith('/var/tmp/kiwi_xslt-')
        assert message == 'Description(XML):'

    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info_print_yaml(self, mock_out):
        self._init_command_args()
        self.task.command_args['--print-yaml'] = True
        self.task.process()
        tmpfile, message = mock_out.display_file.call_args.args
        assert tmpfile.startswith('/var/tmp/kiwi_xslt-')
        assert message == 'Description(YAML):'

    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info_print_toml(self, mock_out):
        self._init_command_args()
        self.task.command_args['--print-toml'] = True
        self.task.process()
        tmpfile, message = mock_out.display_file.call_args.args
        assert tmpfile.startswith('/var/tmp/kiwi_xslt-')
        assert message == 'Description(TOML):'
