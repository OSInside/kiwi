import io
from pytest import raises
from unittest.mock import (
    patch, Mock, MagicMock, call
)

from kiwi.utils.signature import Signature
from kiwi.exceptions import KiwiCredentialsError


class TestSignature:
    def setup(self):
        self.signature = Signature('/some/file')

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.utils.signature.RuntimeConfig')
    def test_sign_raises(self, mock_RuntimeConfig):
        runtime_config = Mock()
        runtime_config.\
            get_credentials_verification_metadata_signing_key_file = Mock(
                return_value=None
            )
        mock_RuntimeConfig.return_value = runtime_config
        with raises(KiwiCredentialsError):
            self.signature.sign()

    @patch('kiwi.utils.signature.RuntimeConfig')
    @patch('kiwi.utils.signature.Command')
    @patch('kiwi.utils.signature.Temporary.new_file')
    def test_sign_verification_metadata(
        self, mock_Temporary_new_file, mock_Command, mock_RuntimeConfig
    ):
        signature_file = Mock()
        signature_file.name = 'signature_file'
        mock_Temporary_new_file.return_value = signature_file
        runtime_config = Mock()
        runtime_config.\
            get_credentials_verification_metadata_signing_key_file = Mock(
                return_value='signing_key_file'
            )
        mock_RuntimeConfig.return_value = runtime_config
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.signature.sign()
        mock_Command.run.assert_called_once_with(
            [
                'openssl', 'dgst', '-sha256',
                '-sigopt', 'rsa_padding_mode:pss',
                '-sigopt', 'rsa_pss_saltlen:-1',
                '-sigopt', 'rsa_mgf1_md:sha256',
                '-sign', 'signing_key_file',
                '-out', 'signature_file',
                '/some/file'
            ]
        )
        assert mock_open.call_args_list == [
            call('signature_file', 'rb'),
            call('/some/file', 'ab')
        ]
        file_handle.write.assert_called_once_with(
            file_handle.read.return_value
        )
