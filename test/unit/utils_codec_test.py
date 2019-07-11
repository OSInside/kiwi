from mock import patch

from .test_helper import raises

from kiwi.utils.codec import Codec
from kiwi.exceptions import KiwiDecodingError


class TestCodec(object):

    def setup(self):
        self.literal = bytes(b'\xc3\xbc')

    @patch('kiwi.utils.codec.Codec._wrapped_decode')
    @patch('kiwi.logger.log.warning')
    def test_decode_ascii_failure(self, mock_warn, mock_decode):
        msg = 'utf-8 compatible string'

        def mocked_decode(literal, charset):
            if charset:
                return msg
            else:
                raise KiwiDecodingError('ascii decoding failure')

        mock_decode.side_effect = mocked_decode
        assert msg == Codec.decode(self.literal)
        assert mock_warn.called

    def test_decode_None_literal(self):
        assert '' == Codec.decode(None)

    @patch('kiwi.utils.codec.Codec._wrapped_decode')
    def test_decode(self, mock_decode):
        msg = 'utf-8 compatible string'
        mock_decode.return_value = msg
        assert msg == Codec.decode(self.literal)

    @raises(KiwiDecodingError)
    @patch('kiwi.utils.codec.Codec._wrapped_decode')
    @patch('kiwi.logger.log.warning')
    def test_decode_utf8_failure(self, mock_warn, mock_decode):

        def mocked_decode(literal, charset):
            if charset:
                raise KiwiDecodingError('utf-8 decoding failure')
            else:
                raise KiwiDecodingError('ascii decoding failure')

        mock_decode.side_effect = mocked_decode
        Codec.decode(self.literal)
        assert mock_warn.called

    def test_wrapped_decode(self):
        assert self.literal.decode() == Codec._wrapped_decode(
            self.literal, 'utf-8'
        )
