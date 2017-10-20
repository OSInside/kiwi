"""
usage: kiwicompat -h | --help
       kiwicompat --build=<description> --dest-dir=<destination>
           [--ignore-repos]
           [(--set-repo=<uri> [--set-repoalias=<alias>] [--set-repopriority=<priority>] [--set-repotype=<type>])]
           [(--add-repo=<uri> [--add-repoalias=<alias>] [--add-repopriority=<priority>] [--add-repotype=<type>])]...
           [--type=<image-type>]
           [--logfile=<filename>]
           [--add-profile=<profile-name>...]
           [--debug]
       kiwicompat --prepare=<description> --root=<image-root>
           [--recycle-root]
           [--logfile=<filename>]
           [--add-profile=<profile-name>...]
           [--ignore-repos]
           [(--set-repo=<uri> [--set-repoalias=<alias>] [--set-repopriority=<priority>] [--set-repotype=<type>])]
           [(--add-repo=<uri> [--add-repoalias=<alias>] [--add-repopriority=<priority>] [--add-repotype=<type>])]...
           [--debug]
       kiwicompat --create=<image-root> --dest-dir=<destination>
           [--ignore-repos]
           [(--set-repo=<uri> [--set-repoalias=<alias>] [--set-repopriority=<priority>] [--set-repotype=<type>])]
           [(--add-repo=<uri> [--add-repoalias=<alias>] [--add-repopriority=<priority>] [--add-repotype=<type>])]...
           [--type=<image-type>]
           [--logfile=<filename>]
           [--add-profile=<profile-name>...]
           [--debug]
       kiwicompat --upgrade=<image-root>
           [--add-package=<name>...]
           [--del-package=<name>...]
           [--logfile=<filename>]
           [--add-profile=<profile-name>...]
           [--debug]
       kiwicompat -v | --version

options:
    -p | --prepare
    -c | --create
    -b | --build
    -d | --dest-dir
    -t | --type
    -u | --upgrade
    -l | --logfile
    -v --version
"""
import os
import logging
from docopt import docopt
from docopt import DocoptExit

# project
from .path import Path


class Cli(object):
    """
        Compatibility class for old style kiwi calls
    """
    def __init__(self):
        try:
            self.compat_args = docopt(
                __doc__, options_first=True
            )
        except DocoptExit as e:
            message_header = '\n'.join(
                [
                    'The provided legacy kiwi commandline is invalid',
                    'or not supported. Plase check the following usage',
                    'information if you just mistyped the call:'
                ]
            )
            message_footer = '\n'.join(
                [
                    'In case of a correct legacy kiwi command but not',
                    'supported by kiwicompat, please contact us via the',
                    'github issue system at:\n',
                    'https://github.com/SUSE/kiwi/issues'
                ]
            )
            raise NotImplementedError(
                '%s\n\n%s\n\n%s' %
                (message_header, format(e), message_footer)
            )


class Translate(object):
    def __init__(self, arguments):
        self.arguments = arguments

        self.translated = []
        if self.arguments['--version']:
            self.translated.append('--version')
        if self.arguments['--logfile']:
            self.translated.append('--logfile')
            self.translated.append(self.arguments['--logfile'])
        if self.arguments['--debug']:
            self.translated.append('--debug')
        if self.arguments['--type']:
            self.translated.append('--type')
            self.translated.append(self.arguments['--type'])
        if self.arguments['--add-profile']:
            for profile in self.arguments['--add-profile']:
                self.translated.append('--profile')
                self.translated.append(profile)

        if self.arguments['--create']:
            self.create(self.arguments['--create'])
        elif self.arguments['--prepare']:
            self.prepare(self.arguments['--prepare'])
        elif self.arguments['--upgrade']:
            self.upgrade(self.arguments['--upgrade'])
        elif self.arguments['--build']:
            self.build(self.arguments['--build'])

    def build(self, description):
        self.translated.append('system')
        self.translated.append('build')
        self.translated.append('--description')
        self.translated.append(description)
        self.translated.append('--target-dir')
        self.translated.append(self.arguments['--dest-dir'])
        if self.arguments['--ignore-repos']:
            self.translated.append('--ignore-repos')
        self._set_add_repo_arguments()

    def create(self, root):
        # Note:
        # --ignore-repos, --set-repo and --add-repo
        # options are allowed to be specified for compatibility reasons
        # but are not used in the next generation kiwi because the repo
        # information is persistently stored after the prepare step
        # has finished, which is not the case for the legacy kiwi
        # version
        self.translated.append('system')
        self.translated.append('create')
        self.translated.append('--root')
        self.translated.append(root)
        self.translated.append('--target-dir')
        self.translated.append(self.arguments['--dest-dir'])

    def prepare(self, description):
        self.translated.append('system')
        self.translated.append('prepare')
        self.translated.append('--description')
        self.translated.append(description)
        self.translated.append('--root')
        self.translated.append(self.arguments['--root'])
        if self.arguments['--ignore-repos']:
            self.translated.append('--ignore-repos')
        if self.arguments['--recycle-root']:
            self.translated.append('--allow-existing-root')
        self._set_add_repo_arguments()

    def upgrade(self, root):
        self.translated.append('system')
        self.translated.append('update')
        self.translated.append('--root')
        self.translated.append(root)
        if self.arguments['--add-package']:
            for add_package in self.arguments['--add-package']:
                self.translated.append('--add-package')
                self.translated.append(add_package)
        if self.arguments['--del-package']:
            for del_package in self.arguments['--del-package']:
                self.translated.append('--delete-package')
                self.translated.append(del_package)

    def _set_add_repo_arguments(self):
        if self.arguments['--add-repo']:
            for index in range(0, len(self.arguments['--add-repo'])):
                repo_type = None
                repo_alias = None
                repo_prio = None
                try:
                    repo_type = self.arguments['--add-repotype'][index]
                except Exception:
                    pass
                try:
                    repo_alias = self.arguments['--add-repoalias'][index]
                except Exception:
                    pass
                try:
                    repo_prio = self.arguments['--add-repopriority'][index]
                except Exception:
                    pass

                self.translated.append('--add-repo')
                self.translated.append(self._repo_argument(
                    self.arguments['--add-repo'][index],
                    repo_type, repo_alias, repo_prio
                ))

        if self.arguments['--set-repo']:
            self.translated.append('--set-repo')
            self.translated.append(self._repo_argument(
                self.arguments['--set-repo'],
                self.arguments['--set-repotype'],
                self.arguments['--set-repoalias'],
                self.arguments['--set-repopriority']
            ))

    def _repo_argument(self, source, repo_type, alias, priority):
        if not repo_type:
            repo_type = ''
        if not alias:
            alias = ''
        if not priority:
            priority = ''
        return ','.join(
            [source, repo_type, alias, priority]
        )


class Command(object):
    @classmethod
    def execute(self, arguments):
        os.execvp(Command.lookup_kiwi(), ['kiwi'] + arguments)

    @classmethod
    def lookup_kiwi(self):
        for kiwi_name in ['kiwi-ng-3', 'kiwi-ng-2']:
            kiwi = Path.which(kiwi_name, access_mode=os.X_OK)
            if kiwi:
                return kiwi
        raise OSError('kiwi not found')


def main():
    logging.basicConfig(format='%(message)s', level=logging.INFO)

    try:
        app = Cli()
        arguments = Translate(app.compat_args)
        # logging.info('Calling: kiwi %s', ' '.join(arguments.translated))
        Command.execute(arguments.translated)
    except NotImplementedError as e:
        logging.error('KiwiCompatError: %s', format(e))
    except OSError as e:
        logging.error('KiwiCompatError: %s', format(e))
