# Copyright (c) 2026 SUSE LLC.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
import sys
import time
import logging
from typing import Callable, Dict, Optional, Tuple

from rich.console import Console
from rich.text import Text

# Width of the time stamp column, HH:MM:SS plus one space
TIME_COLUMN = 9

# Symbols to group the console output, with an ASCII variant
# for consoles which can't encode them
SYMBOLS: Dict[str, Dict[str, str]] = {
    'unicode': {
        'phase': '◆',
        'open': '┌',
        'fork': '┬',
        'branch': '├─',
        'last': '└─',
        'pipe': '│ ',
        'done': '✔',
        'failed': '✘',
        'info': '•',
        'warning': '⚠',
        'error': '✘',
        'debug': '·',
        'checked': '✔',
        'unchecked': '✘',
    },
    'ascii': {
        'phase': '*',
        'open': '+',
        'fork': '+',
        'branch': '|-',
        'last': '`-',
        'pipe': '| ',
        'done': '+',
        'failed': 'x',
        'info': '*',
        'warning': '!',
        'error': 'x',
        'debug': '-',
        'checked': '[x]',
        'unchecked': '[ ]',
    },
}

# Width of the key column of information list items, see Logger.item
ITEM_KEY_WIDTH = 17

# Minimum time an action has to take to show its end on the console,
# see ConsoleRenderer
ACTION_END_MINIMUM_SECONDS = 3.0


class KiwiConsole:
    """
    **Console for the kiwi log and progress output**

    Log messages and progress information are written through the
    same rich consoles, such that log messages are shown above a
    running progress display instead of breaking it up. Colors are
    used if the console is a terminal and the NO_COLOR environment
    variable is not set
    """

    stdout: Console = Console(
        file=sys.__stdout__, highlight=False, soft_wrap=True
    )
    stderr: Console = Console(
        file=sys.__stderr__, highlight=False, soft_wrap=True
    )

    @classmethod
    def colors_enabled(cls) -> bool:
        """
        Colors are used on the console

        :return: True if stdout is a terminal and NO_COLOR is not set

        :rtype: bool
        """
        return cls.stdout.is_terminal and not cls.stdout.no_color

    @staticmethod
    def symbols(console: Console) -> Dict[str, str]:
        """
        Symbols to group the output on the given console

        :param Console console: rich console

        :return: symbol by purpose

        :rtype: dict
        """
        if 'utf' in (console.encoding or '').lower():
            return SYMBOLS['unicode']
        return SYMBOLS['ascii']


class ConsoleRenderer:
    """
    **Renders log records for the console**

    The rendering shows the messages as a tree, grouped by the build
    phase and the step of the build process the message belongs to,
    see Logger.phase and Logger.step:

    * A phase is the root of a tree, its messages and steps are
      shown as branches below it
    * A step is a branch with its messages shown below it. As the
      messages are shown when they are logged, the end of the step
      with the time it took closes the branch
    * Items of an information list are shown as a table, the key
      of consecutive items with the same key is shown only once
    * A message outside of a step announces an action, e.g
      Creating XZ compressed tar archive. If the next message comes
      at least ACTION_END_MINIMUM_SECONDS later, the end of the action
      is shown with the time it took before the next message. This
      way long running actions which are not a step are visible too

    :param callable get_position:
        returns if a phase is active and the number of active steps
    """

    def __init__(self, get_position: Callable[[], Tuple[bool, int]]) -> None:
        self.get_position = get_position
        self.action: Optional[Tuple[str, float]] = None
        self.item_key = ''

    def render(self, record: logging.LogRecord, console: Console) -> Text:
        """
        Render the given log record, preceded by the end of the
        action announced before if it took a while

        :param LogRecord record: log record
        :param Console console: console the record is written to

        :return: rich text

        :rtype: Text
        """
        text = self._render_record(record, console)
        role = getattr(record, 'kiwi_role', '')
        self.item_key = (
            getattr(record, 'kiwi_key', '') if role == 'item' else ''
        )
        announces_action = (
            record.levelno == logging.INFO
            and not role
            and not self.get_position()[1]
        )
        if self.action and (role or announces_action):
            action_end = self._render_action_end(record, console)
            if action_end:
                text = Text.assemble(action_end, '\n', text)
            self.action = None
        if announces_action:
            self.action = (record.getMessage(), record.created)
        return text

    def _render_action_end(
        self, record: logging.LogRecord, console: Console
    ) -> Optional[Text]:
        assert self.action
        message, started = self.action
        duration = record.created - started
        if duration < ACTION_END_MINIMUM_SECONDS:
            return None
        symbol = KiwiConsole.symbols(console)
        text = self._start(record, symbol, self._levels(), stamp=True)
        text.append(f'{symbol["done"]} ', style='green')
        text.append(message)
        text.append(f' ({format_duration(duration)})', style='dim')
        return text

    def _levels(self) -> int:
        phase_active, steps = self.get_position()
        return int(phase_active) + steps

    @staticmethod
    def _start(
        record: logging.LogRecord,
        symbol: Dict[str, str],
        levels: int,
        stamp: bool,
        connector: str = 'branch',
    ) -> Text:
        """
        Start of a line: the time stamp column and the tree branches
        of a message at the given number of tree levels below the root
        """
        text = Text(
            (
                time.strftime('%H:%M:%S ', time.localtime(record.created))
                if stamp
                else ' ' * TIME_COLUMN
            ),
            style='dim',
        )
        if levels:
            text.append(
                symbol['pipe'] * (levels - 1) + symbol[connector] + ' ',
                style='dim',
            )
        return text

    def _render_record(
        self, record: logging.LogRecord, console: Console
    ) -> Text:
        """
        Render the given log record

        :param LogRecord record: log record
        :param Console console: console the record is written to

        :return: rich text

        :rtype: Text
        """
        symbol = KiwiConsole.symbols(console)
        role = getattr(record, 'kiwi_role', '')
        title = getattr(record, 'kiwi_title', '') or record.getMessage()
        message = record.getMessage()
        steps = self.get_position()[1]
        levels = self._levels()

        if role == 'phase':
            text = self._start(record, symbol, 0, stamp=True)
            text.append(f'{symbol["phase"]} {title}', style='bold cyan')
            return text
        if role == 'item':
            return self._render_item(record, symbol, levels)
        if role == 'step_start':
            if levels:
                text = self._start(record, symbol, levels, stamp=True)
                # the branch of the step forks into its messages
                text.right_crop(1)
                text.append(f'{symbol["fork"]} ', style='dim')
            else:
                text = self._start(record, symbol, 0, stamp=True)
                text.append(f'{symbol["open"]} ', style='dim')
            text.append(title, style='bold')
            return text
        if role in ('step_done', 'step_failed'):
            # the end of the step is its last message
            text = self._start(
                record, symbol, levels + 1, stamp=True, connector='last'
            )
            failed = role == 'step_failed'
            text.append(
                f'{symbol["failed" if failed else "done"]} ',
                style='bold red' if failed else 'bold green',
            )
            text.append(title + (' failed' if failed else ''))
            duration = getattr(record, 'kiwi_duration', 0.0)
            text.append(f' ({format_duration(duration)})', style='dim')
            return text
        if record.levelno == logging.ERROR:
            return self._line(record, symbol, levels, 'error', message, 'red')
        if record.levelno == logging.WARNING:
            return self._line(
                record, symbol, levels, 'warning', message, 'yellow'
            )
        if record.levelno == logging.DEBUG:
            return self._line(record, symbol, levels, 'debug', message, 'dim')
        # messages of a step are shown without a time stamp
        text = self._start(record, symbol, levels, stamp=not steps)
        if not levels:
            text.append(f'{symbol["info"]} ')
        text.append(message)
        return text

    def _render_item(
        self, record: logging.LogRecord, symbol: Dict[str, str], levels: int
    ) -> Text:
        key = getattr(record, 'kiwi_key', '')
        checked = getattr(record, 'kiwi_checked', None)
        continued = key == self.item_key
        text = self._start(
            record,
            symbol,
            levels,
            stamp=False,
            connector='pipe' if continued else 'branch',
        )
        text.append(
            ('' if continued else key).ljust(ITEM_KEY_WIDTH), style='bold'
        )
        if checked is not None:
            text.append(
                f'{symbol["checked" if checked else "unchecked"]} ',
                style='green' if checked else 'dim',
            )
        text.append(
            getattr(record, 'kiwi_value', ''),
            style='' if checked is not False else 'dim',
        )
        return text

    def _line(
        self,
        record: logging.LogRecord,
        symbol: Dict[str, str],
        levels: int,
        kind: str,
        message: str,
        style: str,
    ) -> Text:
        text = self._start(record, symbol, levels, stamp=True)
        text.append(f'{symbol[kind]} {message}', style=style)
        return text


class ConsoleHandler(logging.Handler):
    """
    **Logging handler for the kiwi console**

    Writes the log records rendered by ConsoleRenderer to the
    shared kiwi console, see KiwiConsole

    :param ConsoleRenderer renderer: renderer for the records
    :param str channel: stdout or stderr
    """

    def __init__(
        self, renderer: ConsoleRenderer, channel: str = 'stdout'
    ) -> None:
        logging.Handler.__init__(self)
        self.renderer = renderer
        self.channel = channel

    def emit(self, record: logging.LogRecord) -> None:
        try:
            console = self.get_console()
            console.print(self.renderer.render(record, console))
        except Exception:
            self.handleError(record)

    def get_console(self) -> Console:
        return getattr(KiwiConsole, self.channel)


def format_duration(seconds: float) -> str:
    """
    Duration in a short human readable form, e.g 0.4s, 25s or 2m05s

    :param float seconds: duration

    :return: formatted duration

    :rtype: str
    """
    if seconds < 10:
        return f'{seconds:.1f}s'
    if seconds < 60:
        return f'{int(seconds)}s'
    minutes, rest = divmod(int(seconds), 60)
    if minutes < 60:
        return f'{minutes}m{rest:02d}s'
    hours, minutes = divmod(minutes, 60)
    return f'{hours}h{minutes:02d}m'


def get_progress_indent(phase_active: bool = False, steps: int = 0) -> str:
    """
    Indentation of a progress display, continues the tree branches
    of the phase and the steps it is shown in, see ConsoleRenderer

    :param bool phase_active: progress is shown in a phase
    :param int steps: number of active steps

    :return: indentation string

    :rtype: str
    """
    symbol = KiwiConsole.symbols(KiwiConsole.stdout)
    return ' ' * TIME_COLUMN + symbol['pipe'] * (int(phase_active) + steps)
