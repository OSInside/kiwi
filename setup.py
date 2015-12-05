try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from kiwi.version import __VERSION__

config = {
    'description': 'KIWI - Appliance Builder',
    'author': 'Marcus Schäfer',
    'url': 'https://github.com/openSUSE/kiwi',
    'download_url': 'https://github.com/openSUSE/kiwi',
    'author_email': 'ms@suse.com',
    'version': __VERSION__,
    'install_requires': [
        'docopt==0.6.2',
        'lxml'
    ],
    'packages': ['kiwi'],
    'entry_points': {
        'console_scripts': ['kiwi=kiwi.kiwi:main'],
    },
    'name': 'kiwi'
}

setup(**config)
