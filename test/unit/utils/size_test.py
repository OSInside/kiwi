from pytest import raises

from kiwi.utils.size import StringToSize

from kiwi.exceptions import KiwiSizeError


class TestStringToSize:
    def test_to_bytes(self):
        assert StringToSize.to_bytes('1m') == 1048576
        assert StringToSize.to_bytes('1M') == 1048576
        assert StringToSize.to_bytes('1g') == 1073741824
        assert StringToSize.to_bytes('1G') == 1073741824
        assert StringToSize.to_bytes('1234') == 1234

    def test_to_bytes_returns_int(self):
        # The byte value must be returned as int. Returning a float
        # leads to ugly format output like '1073741824.0' when the
        # value is interpolated into shell commands or log messages
        assert isinstance(StringToSize.to_bytes('1'), int)
        assert isinstance(StringToSize.to_bytes('1m'), int)
        assert isinstance(StringToSize.to_bytes('1M'), int)
        assert isinstance(StringToSize.to_bytes('1g'), int)
        assert isinstance(StringToSize.to_bytes('1G'), int)

    def test_to_bytes_wrong_format(self):
        with raises(KiwiSizeError):
            StringToSize.to_bytes('1mb')
