#!/usr/bin/python3
"""
usage: update_changelog (--since=<reference_file>|--file=<reference_file>)
            [--utc]

arguments:
    --since=<reference_file>
        changes since the latest entry in the reference file
    --utc
        print date/time in UTC
"""
import docopt
import os
import subprocess
import sys
from dateutil import parser
from dateutil import tz

# Commandline arguments
arguments = docopt.docopt(__doc__)

# Latest date of the given reference file
date_reference = None

# List of skipped commits older than date_reference
skip_list = []

# hash of git history log entries
log_data = {}

# raw list of log lines from git history or reference file
log_lines = []

# Author and Date
log_author = None
log_date = None

# changelog header line
log_start = '-' * 67 + os.linesep

# date format for rpm changelog
date_format = '%a %b %d %T %Z %Y'

# commit message
commit_message = []

# Open reference log file
reference_file = arguments['--since'] or arguments['--file']

if arguments['--since']:
    # Read latest date from reference file
    with open(reference_file, 'r') as gitlog:
        # read commit and author
        gitlog.readline()
        gitlog.readline()
        # read date
        latest_date = gitlog.readline().replace('AuthorDate:', '').strip()
        date_reference = parser.parse(latest_date)

    # Read git history since latest entry from reference file
    process = subprocess.Popen(
        [
            'git', 'log', '--no-merges', '--format=fuller',
            '--since="{0}"'.format(latest_date)
        ], stdout=subprocess.PIPE
    )
    for line in iter(process.stdout.readline, b''):
        log_lines.append(line)
else:
    with open(reference_file, 'rb') as gitlog:
        log_lines = gitlog.readlines()

# Iterate over log data and convert to changelog format
for line_data in log_lines:
    line = line_data.decode(encoding='utf-8')
    if line.startswith('commit'):
        if commit_message:
            commit_message.pop(0)
            message_header = commit_message.pop(0).lstrip()
            message_body = []
            for line in commit_message:
                message_line = line.lstrip()
                if not message_line:
                    message_body.append(os.linesep)
                else:
                    message_body.append(
                        '  {0}{1}'.format(message_line, os.linesep)
                    )
            log_data[log_date] = ''.join(
                [
                    log_start,
                    '{0} - {1}{2}{2}'.format(
                        log_date.astimezone(
                            tz.UTC if arguments['--utc'] else tz.tzlocal()
                        ).strftime(date_format), log_author, os.linesep
                    ),
                    '- {0}{1}'.format(
                        message_header, os.linesep
                    )
                ] + message_body
            )
            commit_message = []
    elif line.startswith('Author:'):
        log_author = line.replace('Author:', '').strip()
    elif line.startswith('AuthorDate:'):
        log_date = parser.parse(line.replace('AuthorDate:', '').strip())
    elif line.startswith('Commit:'):
        pass
    elif line.startswith('CommitDate:'):
        pass
    else:
        commit_message.append(line.strip())

# print in changelog format on stdout
for author_date in reversed(sorted(log_data.keys())):
    if date_reference:
        if date_reference < author_date:
            sys.stdout.write(log_data[author_date])
        else:
            skip_list.append(author_date)
    else:
        sys.stdout.write(log_data[author_date])

# print inconsistencies if any on stderr
if skip_list:
    sys.stderr.write(
        'Reference Date: {0}{1}'.format(date_reference, os.linesep)
    )
    for date in skip_list:
        sys.stderr.write(
            '  + Skipped: {0}: past reference{1}'.format(
                date, os.linesep
            )
        )
