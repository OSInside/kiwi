from mock import call

import mock

from .test_helper import patch_open

from kiwi.utils.sysconfig import SysConfig


class TestSysConfig(object):
    def setup(self):
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        self.sysconfig = SysConfig('../data/sysconfig_example.txt')

    def test_get_item(self):
        assert self.sysconfig['name'] == ' "Marcus"'

    def test_set_item_existing(self):
        self.sysconfig['name'] = 'Bob'
        assert self.sysconfig['name'] == 'Bob'

    def test_set_item_not_existing(self):
        self.sysconfig['foo'] = '"bar"'
        assert self.sysconfig['foo'] == '"bar"'
        assert self.sysconfig.data_list[-1] == 'foo'

    def test_contains(self):
        assert 'non_existing_key' not in self.sysconfig
        assert 'name' in self.sysconfig

    @patch_open
    def test_write(self, mock_open):
        mock_open.return_value = self.context_manager_mock
        self.sysconfig.write()
        assert self.file_mock.write.call_args_list == [
            call('# some name'),
            call('\n'),
            call('name= "Marcus"'),
            call('\n'),
            call(''),
            call('\n'),
            call('some_key= some-value'),
            call('\n')
        ]
