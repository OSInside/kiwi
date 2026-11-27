import io
import logging
from unittest.mock import patch, Mock

from rich.console import Console

from kiwi.logger_console import (
    ConsoleHandler,
    ConsoleRenderer,
    KiwiConsole,
    format_duration,
    get_progress_indent,
)


class TestConsoleRenderer:
    def setup(self):
        self.phase_active = False
        self.steps = 0
        self.renderer = ConsoleRenderer(lambda: (self.phase_active, self.steps))
        self.console = Console(file=io.StringIO(), width=40, color_system=None)
        self.created = 1700000000.0

    def setup_method(self, cls):
        self.setup()

    def _record(self, message, level=logging.INFO, offset=0.0, **extra):
        record = logging.LogRecord(
            'kiwi', level, __file__, 1, message, None, None
        )
        record.created = self.created + offset
        for key, value in extra.items():
            setattr(record, key, value)
        return record

    def _render(self, message, **kwargs):
        record = self._record(message, **kwargs)
        return self.renderer.render(record, self.console).plain

    @patch('kiwi.logger_console.time.localtime')
    def test_render_root(self, mock_localtime):
        mock_localtime.return_value = (2026, 11, 27, 11, 19, 33, 4, 331, 0)
        # messages and steps outside of a phase
        assert self._render('Set type') == '11:19:33 • Set type'
        assert self._render('Loading', kiwi_role='step_start') == (
            '11:19:33 ┌ Loading'
        )
        self.steps = 1
        assert self._render('loaded config.xml') == (
            '         ├─ loaded config.xml'
        )
        self.steps = 0
        assert self._render(
            'Loading: done (0.9s)',
            kiwi_role='step_done',
            kiwi_title='Loading',
            kiwi_duration=0.9,
        ) == ('11:19:33 └─ ✔ Loading (0.9s)')

    @patch('kiwi.logger_console.time.localtime')
    def test_render(self, mock_localtime):
        mock_localtime.return_value = (2026, 11, 27, 11, 19, 33, 4, 331, 0)
        assert self._render('Prepare root system', kiwi_role='phase') == (
            '11:19:33 ◆ Prepare root system'
        )
        self.phase_active = True
        assert self._render('Setup root directory') == (
            '11:19:33 ├─ Setup root directory'
        )
        assert self._render('Bootstrap', kiwi_role='step_start') == (
            '11:19:33 ├─┬ Bootstrap'
        )
        self.steps = 1
        # messages of a step are shown as its branches
        assert self._render('collection type') == (
            '         │ ├─ collection type'
        )
        assert self._render('a warning', level=logging.WARNING) == (
            '11:19:33 │ ├─ ⚠ a warning'
        )
        assert self._render('an error', level=logging.ERROR) == (
            '11:19:33 │ ├─ ✘ an error'
        )
        assert self._render('EXEC: [ls]', level=logging.DEBUG) == (
            '11:19:33 │ ├─ · EXEC: [ls]'
        )
        assert self._render('Partitions', kiwi_role='step_start') == (
            '11:19:33 │ ├─┬ Partitions'
        )
        self.steps = 2
        assert self._render('creating EFI partition') == (
            '         │ │ ├─ creating EFI partition'
        )
        self.steps = 1
        assert self._render(
            'Partitions: failed (2.5s)',
            kiwi_role='step_failed',
            kiwi_title='Partitions',
            kiwi_duration=2.5,
        ) == ('11:19:33 │ │ └─ ✘ Partitions failed (2.5s)')
        self.steps = 0
        # the end of the step closes its branch
        assert self._render(
            'Bootstrap: done (25s)',
            kiwi_role='step_done',
            kiwi_title='Bootstrap',
            kiwi_duration=25.0,
        ) == ('11:19:33 │ └─ ✔ Bootstrap (25s)')

    @patch('kiwi.logger_console.time.localtime')
    def test_render_action_end(self, mock_localtime):
        mock_localtime.return_value = (2026, 11, 27, 11, 20, 42, 4, 331, 0)
        self.phase_active = True
        self._render('Creating XZ compressed tar archive')
        # warnings and debug messages belong to the action
        self._render('warning', level=logging.WARNING, offset=10)
        self._render('debug', level=logging.DEBUG, offset=20)
        # the next message shows the end of the long running action
        assert self._render('Creating checksum', offset=48).split('\n') == [
            '11:20:42 ├─ ✔ Creating XZ compressed tar archive (48s)',
            '11:20:42 ├─ Creating checksum',
        ]
        # a quick action is not completed explicitly
        assert self._render('Results', kiwi_role='phase', offset=49) == (
            '11:20:42 ◆ Results'
        )
        # messages of a step do not announce an action
        self.steps = 1
        self._render('inside of a step', offset=50)
        self.steps = 0
        assert self.renderer.action is None

    def test_render_item(self):
        self.phase_active = True
        assert (
            self._render(
                'Type: oem', kiwi_role='item', kiwi_key='Type', kiwi_value='oem'
            )
            == ' ' * 9 + '├─ Type             oem'
        )
        assert (
            self._render(
                'Features: [x] LVM',
                kiwi_role='item',
                kiwi_key='Features',
                kiwi_value='LVM',
                kiwi_checked=True,
            )
            == ' ' * 9 + '├─ Features         ✔ LVM'
        )
        # the key of consecutive items is shown once
        assert (
            self._render(
                'Features: [ ] Install ISO',
                kiwi_role='item',
                kiwi_key='Features',
                kiwi_value='Install ISO',
                kiwi_checked=False,
            )
            == ' ' * 9 + '│  ' + ' ' * 17 + '✘ Install ISO'
        )
        self._render('Prepare root system', kiwi_role='phase')
        assert self.renderer.item_key == ''

    @patch('kiwi.logger_console.time.localtime')
    def test_render_ascii(self, mock_localtime):
        mock_localtime.return_value = (2026, 11, 27, 11, 19, 33, 4, 331, 0)
        console = Mock()
        console.encoding = 'ascii'
        self.phase_active = True
        self.steps = 1
        record = self._record('Partitions', kiwi_role='step_start')
        assert self.renderer.render(record, console).plain == (
            '11:19:33 | |-+ Partitions'
        )


class TestConsoleHandler:
    def test_emit(self):
        renderer = Mock()
        handler = ConsoleHandler(renderer, 'stderr')
        record = Mock()
        with patch.object(KiwiConsole, 'stderr') as mock_stderr:
            handler.emit(record)
            renderer.render.assert_called_once_with(record, mock_stderr)
            mock_stderr.print.assert_called_once_with(
                renderer.render.return_value
            )

    def test_emit_error(self):
        renderer = Mock()
        renderer.render.side_effect = Exception
        handler = ConsoleHandler(renderer)
        handler.handleError = Mock()
        record = Mock()
        handler.emit(record)
        handler.handleError.assert_called_once_with(record)


class TestKiwiConsole:
    def test_colors_enabled(self):
        stdout = KiwiConsole.stdout
        try:
            KiwiConsole.stdout = Mock(is_terminal=True, no_color=False)
            assert KiwiConsole.colors_enabled() is True
            # NO_COLOR is set
            KiwiConsole.stdout = Mock(is_terminal=True, no_color=True)
            assert KiwiConsole.colors_enabled() is False
            KiwiConsole.stdout = Mock(is_terminal=False, no_color=False)
            assert KiwiConsole.colors_enabled() is False
        finally:
            KiwiConsole.stdout = stdout


def test_format_duration():
    assert format_duration(0.42) == '0.4s'
    assert format_duration(25.7) == '25s'
    assert format_duration(125) == '2m05s'
    assert format_duration(3725) == '1h02m'


def test_get_progress_indent():
    assert get_progress_indent() == ' ' * 9
    with patch.object(KiwiConsole, 'stdout') as mock_stdout:
        mock_stdout.encoding = 'utf-8'
        # the progress continues the branches of the phase and steps
        assert get_progress_indent(True, 1) == ' ' * 9 + '│ │ '
