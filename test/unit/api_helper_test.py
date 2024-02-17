from pytest import raises
from unittest.mock import patch
from kiwi.api_helper import (
    obsolete,
    decommissioned
)


@decommissioned
def method_decommissioned():
    # Implementation has been deleted
    pass


@obsolete(decommission_at='2025-01-28', version="1.2.3")
def method_obsolete():
    return 'I still exist'


class TestApiHelpers:
    def test_method_decommissioned(self):
        with raises(DeprecationWarning):
            method_decommissioned()

    @patch('warnings.warn')
    def test_method_obsolete(self, mock_warnings_warn):
        warning_message = (
            "Function 'method_obsolete' is marked obsolete "
            "since version '1.2.3' and will be decommissioned "
            "at: 2025-01-28"
        )
        assert method_obsolete() == 'I still exist'
        mock_warnings_warn.assert_called_once_with(warning_message)
