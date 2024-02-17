import logging
from unittest.mock import patch
from pytest import (
    raises, fixture
)

from kiwi.utils.codec import Codec

from kiwi.exceptions import KiwiDecodingError


class TestCodec:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.literal = bytes(b'\xc3\xbc')

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.utils.codec.Codec._wrapped_decode')
    def test_decode_ascii_failure(self, mock_decode):
        msg = 'utf-8 compatible string'

        def mocked_decode(literal, encoding, error_handling_schema):
            if encoding:
                return msg
            else:
                raise KiwiDecodingError('ascii decoding failure')

        mock_decode.side_effect = mocked_decode
        with self._caplog.at_level(logging.WARNING):
            assert msg == Codec.decode(self.literal)

    def test_decode_None_literal(self):
        assert '' == Codec.decode(None)

    @patch('kiwi.utils.codec.Codec._wrapped_decode')
    def test_decode(self, mock_decode):
        msg = 'utf-8 compatible string'
        mock_decode.return_value = msg
        assert msg == Codec.decode(self.literal)

    @patch('kiwi.utils.codec.Codec._wrapped_decode')
    def test_decode_utf8_failure(self, mock_decode):
        def mocked_decode(literal, encoding, error_handling_schema):
            if encoding:
                raise KiwiDecodingError('utf-8 decoding failure')
            else:
                raise KiwiDecodingError('ascii decoding failure')

        mock_decode.side_effect = mocked_decode
        with raises(KiwiDecodingError):
            with self._caplog.at_level(logging.WARNING):
                Codec.decode(self.literal)

    def test_wrapped_decode(self):
        assert self.literal.decode() == Codec._wrapped_decode(
            self.literal, 'utf-8'
        )
