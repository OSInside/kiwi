#!/usr/bin/python3
"""
usage: update_changelog --since=<reference_file>|--until=<reference_file>

arguments:
    --since=<reference_file>
        changes since the latest entry in the reference file
    --until=<reference_file>
        changes until the latest entry in the reference file
"""
import docopt
import os
import subprocess
import sys
from dateutil import parser


# For sorting dates use a timedelta object
def date_key(date_string):
    date_string = parser.parse(date_string)
    return date_string


# Commandline arguments
arguments = docopt.docopt(__doc__)

# Latest date of the given reference file
latest_date = None

# hash of git history log entries
log_data = {}

# Author and Date
log_author = None
log_date = None

# changelog header line
log_start = '-' * 67 + os.linesep

# commit message
commit_message = []

# Open reference changelog file
# This assumes a certain changelog format
reference_file = arguments['--until'] or arguments['--since']
with open(reference_file, 'r') as changelog:
    # read headline of first entry
    changelog.readline()
    # read date of first entry
    latest_date = changelog.readline().split('-')[0]

# Read git history since latest entry from reference log
process = subprocess.Popen(
    [
        'git', 'log', '--topo-order', '--no-merges', '--format=fuller',
        '{0}="{1}"'.format(
            '--until' if arguments['--until'] else '--since', latest_date
        ),
        '--date=format-local:%a %b %d %T %Z %Y'
    ],
    stdout=subprocess.PIPE
)

# Iterate over history and convert to changelog format
for line_data in iter(process.stdout.readline, b''):
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
                        log_date, log_author, os.linesep
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
        log_date = line.replace('AuthorDate:', '').strip()
    elif line.startswith('Commit:'):
        pass
    elif line.startswith('CommitDate:'):
        pass
    else:
        commit_message.append(line.strip())

# print history
for author_date in reversed(sorted(log_data.keys(), key=date_key)):
    sys.stdout.write(log_data[author_date])
