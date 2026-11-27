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
from typing import Dict, List, NamedTuple, Set


class PackageManagerEventT(NamedTuple):
    """
    Progress event, read from a line of package manager output

    :param str phase:
        phase of the package manager run the event belongs to,
        one of the phases the package manager counts, see
        PackageManagerBase.progress_phases, or 'script' for package
        scripts, triggers and hooks, or 'total' if the event only
        announces the number of packages
    :param str description: text to show, e.g Installing bash
    :param int current:
        position of the event in its phase as reported by the
        package manager, 0 if not reported
    :param int total:
        number of events of the phase as reported by the package
        manager, 0 if not reported. For the 'total' phase the
        number of packages
    :param str package:
        name of the package or script the event is about, if any
    :param bool removed: the event is about a package removal
    """

    phase: str
    description: str = ''
    current: int = 0
    total: int = 0
    package: str = ''
    removed: bool = False


class InstallProgress:
    """
    **Progress of a package manager run**

    Combines the progress events of a package manager run into one
    progress value. Each of the phases the package manager counts,
    e.g downloading and installing, takes an equal part of the
    progress. Within a phase the position reported by the package
    manager is used, or the events of the phase are counted against
    the number of packages if the package manager does not report
    a position. Package scripts, triggers and hooks are shown and
    counted, they only take a part of the progress if the package
    manager counts them as a phase

    :param list phases: phases counted by the package manager
    """

    #: progress value of a complete run
    TOTAL = 1000

    #: highest progress value before the end of the run, shown as 99%
    UNTIL_END = 990

    #: phases in which each package is processed once
    PACKAGE_PHASES = ('install', 'unpack')

    def __init__(self, phases: List[str]) -> None:
        self.phases = phases
        self.description = ''
        self.completed = 0
        self.events_seen = False
        self.packages_total = 0
        self.phase_counts: Dict[str, int] = {}
        self.installed: Set[str] = set()
        self.removed: Set[str] = set()
        self.scripts = 0

    def update(self, event: PackageManagerEventT) -> None:
        """
        Update the progress with the given event

        :param PackageManagerEventT event: progress event
        """
        self.events_seen = True
        if event.phase == 'total':
            self.packages_total = event.total
            return
        if event.description:
            self.description = event.description
            if event.current and event.total:
                self.description = (
                    f'{event.current}/{event.total} {event.description}'
                )
        if event.phase == 'script' and event.package:
            self.scripts += 1
        if event.phase in self.PACKAGE_PHASES and event.package:
            if event.removed:
                self.removed.add(event.package)
            else:
                self.installed.add(event.package)
        if event.phase not in self.phases:
            return
        self.phase_counts[event.phase] = (
            self.phase_counts.get(event.phase, 0) + 1
        )
        current = event.current or self.phase_counts[event.phase]
        total = event.total or self.packages_total
        if not total:
            return
        if event.description:
            self.description = f'{current}/{total} {event.description}'
        position = self.phases.index(event.phase) + min(current / total, 1)
        # the progress is complete with the end of the run only, e.g
        # scripts may still run after the last package, and does not
        # go backwards, e.g if a phase is repeated
        self.completed = max(
            self.completed,
            min(int(position / len(self.phases) * self.TOTAL), self.UNTIL_END),
        )

    def summary(self) -> str:
        """
        Summary of the run, e.g 148 packages installed, 21 scripts run

        :return: summary text, empty if no package was processed

        :rtype: str
        """
        parts = []
        if self.installed:
            parts.append(_count(len(self.installed), 'package') + ' installed')
        if self.removed:
            parts.append(_count(len(self.removed), 'package') + ' removed')
        if self.scripts:
            parts.append(_count(self.scripts, 'script') + ' run')
        return ', '.join(parts)


def _count(number: int, name: str) -> str:
    return f'{number} {name}' + ('' if number == 1 else 's')
