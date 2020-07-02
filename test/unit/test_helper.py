import sys

# default commandline used for any test, overwrite when needed
sys.argv = [
    sys.argv[0], 'system', 'prepare',
    '--description', 'description', '--root', 'directory'
]
argv_kiwi_tests = sys.argv
