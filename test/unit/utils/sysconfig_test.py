from mock import (
    call, mock_open, patch
)

from kiwi.utils.sysconfig import SysConfig


class TestSysConfig:
    def setup(self):
        self.sysconfig = SysConfig('../data/sysconfig_example.txt')

    def test_get_item(self):
        assert self.sysconfig['name'] == ' "Marcus"'
        assert self.sysconfig.get('name') == ' "Marcus"'

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

    def test_write(self):
        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            self.sysconfig.write()

        assert m_open.return_value.write.call_args_list == [
            call('# some name'),
            call('\n'),
            call('name= "Marcus"'),
            call('\n'),
            call(''),
            call('\n'),
            call('some_key= some-value'),
            call('\n')
        ]
