import signal
import logging
from unittest.mock import patch, call
from pytest import raises, fixture

from kiwi.kiwi import KiwiTerminated, main, terminate


class TestKiwi:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.kiwi.signal.signal')
    def test_terminate(self, mock_signal):
        with raises(KiwiTerminated) as issue:
            terminate(signal.SIGTERM, None)
        assert issue.value.signum == signal.SIGTERM
        assert format(issue.value) == 'SIGTERM'
        # another signal of this kind ends kiwi immediately
        mock_signal.assert_called_once_with(signal.SIGTERM, signal.SIG_DFL)
        # the signal is not handled as error by kiwi code
        assert not isinstance(issue.value, Exception)

    @patch('kiwi.kiwi.signal.signal')
    @patch('kiwi.kiwi.App')
    def test_main_terminated(self, mock_App, mock_signal):
        mock_App.side_effect = KiwiTerminated(signal.SIGHUP)
        with self._caplog.at_level(logging.ERROR):
            with raises(SystemExit) as issue:
                main()
        assert mock_signal.call_args_list == [
            call(signal.SIGTERM, terminate),
            call(signal.SIGHUP, terminate),
        ]
        assert issue.value.code == 128 + signal.SIGHUP
        assert 'kiwi terminated by signal SIGHUP' in self._caplog.text
