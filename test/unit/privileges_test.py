from mock import patch

from .test_helper import raises

from kiwi.exceptions import KiwiPrivilegesError
from kiwi.privileges import Privileges


class TestPrivileges(object):
    @raises(KiwiPrivilegesError)
    @patch('os.geteuid')
    def test_check_for_root_permiossion_false(self, mock_euid):
        mock_euid.return_value = 1
        Privileges.check_for_root_permissions()

    @patch('os.geteuid')
    def test_check_for_root_permiossion_true(self, mock_euid):
        mock_euid.return_value = 0
        assert Privileges.check_for_root_permissions() is True
