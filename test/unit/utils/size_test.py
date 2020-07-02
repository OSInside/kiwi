from pytest import raises

from kiwi.utils.size import StringToSize

from kiwi.exceptions import KiwiSizeError


class TestStringToSize:
    def test_to_bytes(self):
        assert StringToSize.to_bytes('1m') == 1048576
        assert StringToSize.to_bytes('1M') == 1048576
        assert StringToSize.to_bytes('1g') == 1073741824
        assert StringToSize.to_bytes('1G') == 1073741824

    def test_to_bytes_wrong_format(self):
        with raises(KiwiSizeError):
            StringToSize.to_bytes('1mb')
