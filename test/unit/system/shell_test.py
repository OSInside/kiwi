from pytest import raises

from kiwi.system.shell import Shell
from kiwi.exceptions import KiwiShellVariableValueError


class TestSystemShell:
    def test_format_to_variable_value(self):
        assert Shell.format_to_variable_value('text') == 'text'
        assert Shell.format_to_variable_value(True) == 'true'
        assert Shell.format_to_variable_value(False) == 'false'
        assert Shell.format_to_variable_value('42') == '42'
        assert Shell.format_to_variable_value(0) == '0'
        assert Shell.format_to_variable_value(42) == '42'
        assert Shell.format_to_variable_value(None) == ''
        assert Shell.format_to_variable_value(b"42") == '42'
        with raises(KiwiShellVariableValueError):
            Shell.format_to_variable_value(['foo', 'bar'])
