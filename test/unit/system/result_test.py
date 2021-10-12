import logging
from mock import (
    patch, Mock, mock_open, call
)
from pytest import (
    raises, fixture
)

from kiwi.system.result import Result

from kiwi.exceptions import KiwiResultError


class TestResult:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.xml_state = Mock()

        self.result = Result(self.xml_state)

    def test_add(self):
        assert self.result.add('foo', 'bar') is None
        result = self.result.get_results()
        assert isinstance(result, dict)
        assert result['foo'].filename == 'bar'
        assert result['foo'].use_for_bundle is True
        assert result['foo'].compress is False

    def test_print_results_no_data(self):
        assert self.result.print_results() is None
        assert not self._caplog.text

    def test_print_results_data(self):
        assert self.result.add('foo', 'bar') is None
        with self._caplog.at_level(logging.INFO):
            self.result.print_results()

    @patch('pickle.dump')
    @patch('simplejson.dumps')
    def test_dump(self, mock_simplejson_dumps, mock_pickle_dump):
        m_open = mock_open()
        with patch('builtins.open', m_open, create=True):
            assert self.result.dump('kiwi.result') is None

        assert m_open.call_args_list == [
            call('kiwi.result', 'wb'),
            call('kiwi.result.json', 'w')
        ]
        mock_pickle_dump.assert_called_once_with(
            self.result, m_open.return_value
        )
        mock_simplejson_dumps.assert_called_once_with(
            self.result.result_files, sort_keys=True, indent=4
        )

    @patch('pickle.dump')
    def test_dump_failed(self, mock_pickle_dump):
        mock_pickle_dump.side_effect = Exception
        with patch('builtins.open'):
            with raises(KiwiResultError):
                self.result.dump('kiwi.result')

    @patch('pickle.load')
    @patch('os.path.exists')
    def test_load(self, mock_exists, mock_pickle_load):
        mock_exists.return_value = True

        m_open = mock_open()
        mock_pickle_load.return_value = Result
        with patch('builtins.open', m_open, create=True):
            assert Result.load('kiwi.result') is Result

        m_open.assert_called_once_with(
            'kiwi.result', 'rb'
        )
        mock_pickle_load.assert_called_once_with(
            m_open.return_value
        )

    @patch('os.path.exists')
    def test_load_result_not_present(self, mock_exists):
        mock_exists.return_value = False
        with raises(KiwiResultError):
            Result.load('kiwi.result')

    @patch('pickle.load')
    @patch('os.path.exists')
    def test_load_failed(self, mock_exists, mock_pickle_load):
        mock_exists.return_value = True
        mock_pickle_load.side_effect = Exception
        with raises(KiwiResultError):
            Result.load('kiwi.result')

    @patch('os.path.getsize')
    def test_build_constraint(self, mock_getsize):
        mock_getsize.return_value = 524288000
        assert self.result.verify_image_size(524288000, 'foo') is None

    @patch('os.path.getsize')
    def test_build_constraint_failure(self, mock_getsize):
        mock_getsize.return_value = 524288000
        with raises(KiwiResultError):
            self.result.verify_image_size(524287999, 'foo')
