import sys
import mock

from mock import patch, call

import kiwi

from .test_helper import argv_kiwi_tests

from kiwi.tasks.image_info import ImageInfoTask

from collections import namedtuple


class TestImageInfoTask(object):
    def setup(self):
        sys.argv = [
            sys.argv[0], '--profile', 'vmxFlavour', 'image', 'info',
            '--description', '../data/description',
            '--resolve-package-list'
        ]
        result_type = namedtuple(
            'result_type', [
                'uri', 'installsize_bytes', 'arch', 'version', 'checksum'
            ]
        )
        self.result_info = {
            'image': 'LimeJeOS-openSUSE-13.2',
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
        self.runtime_checker = mock.Mock()
        kiwi.tasks.base.RuntimeChecker = mock.Mock(
            return_value=self.runtime_checker
        )
        self.runtime_config = mock.Mock()
        kiwi.tasks.base.RuntimeConfig = mock.Mock(
            return_value=self.runtime_config
        )
        self.solver = mock.MagicMock()
        self.solver.solve = mock.Mock(
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
        kiwi.tasks.image_info.Sat = mock.Mock(
            return_value=self.solver
        )

        self.solver_repository = mock.Mock()
        kiwi.tasks.image_info.SolverRepository = mock.Mock(
            return_value=self.solver_repository
        )

        kiwi.tasks.image_info.Help = mock.Mock(
            return_value=mock.Mock()
        )
        self.task = ImageInfoTask()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def _init_command_args(self):
        self.task.command_args = {}
        self.task.command_args['help'] = False
        self.task.command_args['info'] = False
        self.task.command_args['--description'] = '../data/description'
        self.task.command_args['--add-repo'] = []
        self.task.command_args['--ignore-repos'] = False
        self.task.command_args['--resolve-package-list'] = False

    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info(self, mock_out):
        self._init_command_args()
        self.task.command_args['info'] = True
        self.task.process()
        self.runtime_checker.check_repositories_configured.assert_called_once_with()
        mock_out.assert_called_once_with(
            {'image': 'LimeJeOS-openSUSE-13.2'}
        )

    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info_color_output(self, mock_out):
        self._init_command_args()
        self.task.command_args['info'] = True
        self.task.global_args['--color-output'] = True
        self.task.process()
        mock_out.assert_called_once_with(
            {'image': 'LimeJeOS-openSUSE-13.2'}, style='color'
        )

    @patch('kiwi.tasks.image_info.DataOutput')
    @patch('kiwi.tasks.image_info.SolverRepository')
    @patch('kiwi.tasks.image_info.Uri')
    def test_process_image_info_resolve_package_list(
        self, mock_uri, mock_solver_repo, mock_out
    ):
        self._init_command_args()
        self.task.command_args['info'] = True
        self.task.command_args['--resolve-package-list'] = True
        self.task.process()
        assert self.solver.add_repository.called
        assert mock_uri.call_args_list == [
            call('iso:///image/CDs/dvd.iso', 'yast2'),
            call('obs://Devel:PubCloud:AmazonEC2/SLE_12_GA', 'rpm-md')
        ]
        mock_out.assert_called_once_with(self.result_info)

    @patch('kiwi.xml_state.XMLState.add_repository')
    @patch('kiwi.tasks.image_info.DataOutput')
    def test_process_image_info_add_repo(self, mock_out, mock_state):
        self._init_command_args()
        self.task.command_args['--add-repo'] = [
            'http://example.com,yast2,alias'
        ]
        self.task.process()
        mock_state.assert_called_once_with(
            'http://example.com', 'yast2', 'alias', None
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
