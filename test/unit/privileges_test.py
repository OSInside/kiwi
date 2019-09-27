from mock import patch
from pytest import raises

from kiwi.privileges import Privileges

from kiwi.exceptions import KiwiPrivilegesError


class TestPrivileges:
    @patch('os.geteuid')
    def test_check_for_root_permiossion_false(self, mock_euid):
        mock_euid.return_value = 1
        with raises(KiwiPrivilegesError):
            Privileges.check_for_root_permissions()

    @patch('os.geteuid')
    def test_check_for_root_permiossion_true(self, mock_euid):
        mock_euid.return_value = 0
        assert Privileges.check_for_root_permissions() is True
