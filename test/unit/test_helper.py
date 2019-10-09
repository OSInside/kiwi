import kiwi.logger
import sys
import logging

# default log level, overwrite when needed
kiwi.logger.log.setLevel(logging.WARN)

# default commandline used for any test, overwrite when needed
sys.argv = [
    sys.argv[0], 'system', 'prepare',
    '--description', 'description', '--root', 'directory'
]
argv_kiwi_tests = sys.argv
