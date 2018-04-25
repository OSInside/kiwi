from .test_helper import raises

from kiwi.utils.size import StringToSize
from kiwi.exceptions import KiwiSizeError


class TestStringToSize(object):

    def test_to_bytes(self):
        assert StringToSize.to_bytes('1m') == 1048576
        assert StringToSize.to_bytes('1M') == 1048576
        assert StringToSize.to_bytes('1g') == 1073741824
        assert StringToSize.to_bytes('1G') == 1073741824

    @raises(KiwiSizeError)
    def test_to_bytes_wrong_format(self):
        StringToSize.to_bytes('1mb')
