# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
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
import typer
import logging
import sys
import os
from unittest.mock import patch
from importlib.metadata import (
    entry_points, EntryPoint
)
from pathlib import Path
from typing import (
    Annotated, Dict, Optional, List
)

# project
from kiwi.exceptions import (
    KiwiUnknownServiceName,
    KiwiCommandNotLoaded,
    KiwiLoadCommandUndefined,
    KiwiLoadPluginError
)
from kiwi.version import __version__
# from kiwi.help import Help
from kiwi.defaults import Defaults

log = logging.getLogger('kiwi')


class Cli:
    """
    **Implements the main command line interface**

    An instance of the Cli class builds the entry point for the
    application and implements methods to load further command plugins
    which itself provides their own command line interface
    """
    global_args: Dict = {}
    subcommand_args: Dict = {}
    plugins: Dict[str, typer.Typer] = {}
    cli_ok = False

    # system
    system = typer.Typer(
        help='system command for building images. The system space '
        'can also be extended by custom command plugins.'
    )

    # result
    result = typer.Typer(
        help='result command for listing image result information '
        'and create result bundles.'
    )

    # image
    image = typer.Typer(
        help='image command for retrieving image information '
        'prior building.'
    )

    cli = typer.Typer(add_completion=False)
    cli.add_typer(system, name='system')
    cli.add_typer(result, name='result')
    cli.add_typer(image, name='image')

    def __init__(self):
        Cli.cli_ok = False
        exit_code = 1
        # load plugins...
        Cli.plugins.update(
            self.load_plugin_cli()
        )
        # add plugin cli's if there are any loaded
        for system_subcommand in sorted(Cli.plugins.keys()):
            Cli.system.add_typer(
                Cli.plugins[system_subcommand], name=system_subcommand,
                context_settings={
                    'obj': Cli
                }
            )
        with patch('sys.exit') as sys_exit:
            # This is unfortunately needed to integrate the
            # typer interface with the former docopt based
            # option handling to kiwi in a way that is not
            # too intrusive. Usually typer quits after the
            # invocation of the commmand function. But in case
            # of kiwi we need the result of the typer processing
            # to be used in the task classes such that typer
            # should not exit from its operation.
            Cli.cli()
            (exit_code,) = sys_exit.call_args[0]
        if not Cli.cli_ok:
            sys.exit(exit_code)

        self.command_args = self.get_command_args(
            raise_if_no_command=False
        )
        self.command_loaded = None

    def version(self, perform: bool):
        if perform:
            print(f'KIWI (next generation) version {__version__}')
            raise typer.Exit(0)

    @staticmethod
    @cli.callback()
    def main(
        color_output: Annotated[
            bool, typer.Option(
                '--color-output',
                help='use colors for warning and error messages'
            )
        ] = False,
        config: Annotated[
            Optional[Path], typer.Option(
                help='use specified runtime configuration file. If '
                'not specified the runtime configuration is looked '
                'up at ~/.config/kiwi/config.yml or /etc/kiwi.yml'
            )
        ] = None,
        debug: Annotated[
            bool, typer.Option(
                '--debug',
                help='print debug information, same as: --loglevel 10'
            )
        ] = False,
        debug_run_scripts_in_screen: Annotated[
            bool, typer.Option(
                '--debug-run-scripts-in-screen',
                help='run scripts called by kiwi in a screen session'
            )
        ] = False,
        kiwi_file: Annotated[
            Optional[str], typer.Option(
                help='<kiwifile> Basename of kiwi file which contains '
                'the main image configuration elements. If not specified '
                'kiwi searches for a file named config.xml or a file '
                'matching *.kiwi'
            )
        ] = None,
        logfile: Annotated[
            Optional[Path], typer.Option(
                help='<filename> create a log file containing all log '
                'information including debug information even if this '
                'was not requested by the debug switch. The special '
                'call: "--logfile stdout" sends all information to '
                'standard out instead of writing to a file'
            )
        ] = None,
        logsocket: Annotated[
            Optional[Path], typer.Option(
                help='<socketfile> send log data to the given Unix '
                'Domain socket in the same format as with --logfile'
            )
        ] = None,
        loglevel: Annotated[
            Optional[int], typer.Option(
                help='<number> specify logging level as number. '
                'Details about the available log levels can be found at: '
                'https://docs.python.org/3/library/logging.html#logging-levels '
                'Setting a log level causes all message >= level to be '
                'displayed.'
            )
        ] = None,
        profile: Annotated[
            Optional[List[str]], typer.Option(
                help='<name> Profile name, multiple profiles can be selected '
                'by passing this option multiple times'
            )
        ] = [],
        setenv: Annotated[
            Optional[List[str]], typer.Option(
                help='<variable=value> export environment variable and its '
                'value into the caller environment. This option can be '
                'specified multiple times  '
            )
        ] = [],
        shared_cache_dir: Annotated[
            Optional[Path], typer.Option(
                help='<directory> An alternative shared cache directory. '
                'The directory is shared via bind mount between the '
                'build host and image root system and contains '
                'information about package repositories and their '
                'cache and meta data.'
            )
        ] = Path(os.sep + Defaults.get_shared_cache_location()),
        target_arch: Annotated[
            Optional[str], typer.Option(
                help='<name> set the image architecture. By default the host '
                'architecture is used as the image architecture. If the '
                'specified architecture name does not match the host '
                'architecture and is therefore requesting a cross '
                'architecture image build, it is important to understand '
                'that for this process to work a preparatory step to '
                'support the image architecture and binary format on the '
                'building host is required first.'
            )
        ] = None,
        temp_dir: Annotated[
            Optional[Path], typer.Option(
                help='<directory> An alternative base temporary directory. '
                'The provided path is used as base directory to store '
                'temporary files and directories.'
            )
        ] = Path(Defaults.get_temp_location()),
        type: Annotated[
            Optional[str], typer.Option(
                help='<build_type> Image build type. If not set the '
                'default XML specified build type will be used'
            )
        ] = None,
        version: Annotated[
            Optional[bool], typer.Option(
                '--version', help='show program version', callback=version
            )
        ] = None
    ):
        """
        KIWI - Appliance Builder
        """
        Cli.global_args['--color-output'] = color_output
        Cli.global_args['--config'] = config
        Cli.global_args['--debug'] = debug
        Cli.global_args['--debug-run-scripts-in-screen'] = \
            debug_run_scripts_in_screen
        Cli.global_args['--kiwi-file'] = kiwi_file
        Cli.global_args['--logfile'] = logfile
        Cli.global_args['--loglevel'] = loglevel
        Cli.global_args['--logsocket'] = logsocket
        Cli.global_args['--profile'] = profile
        Cli.global_args['--setenv'] = setenv
        Cli.global_args['--shared-cache-dir'] = f'{shared_cache_dir}'
        Cli.global_args['--target-arch'] = target_arch
        Cli.global_args['--temp-dir'] = f'{temp_dir}'
        Cli.global_args['--type'] = type
        Cli.global_args['command'] = None
        Cli.global_args['image'] = False
        Cli.global_args['result'] = False
        Cli.global_args['system'] = False

    # The following allows to show the kiwi main man page by
    # calling "kiwi-ng help". However I was not able to code typer
    # in a way that the other command specific man pages can be
    # called as e.g. "kiwi image info help". That's because
    # in "kiwi-ng [OPTIONS] COMMAND [ARGS]..." the COMMAND: help
    # can be added. But in "kiwi-ng image info [OPTIONS]", help
    # would be an OPTION and not a COMMAND. I could not come
    # up with a solution to this issue. As such disable calling
    # man pages from calling kiwi completely for now.
    # @staticmethod
    # @cli.command(help='[kiwi::COMMAND:SUBCOMMAND]')
    # def help(command: Annotated[str, typer.Argument()] = 'kiwi'):
    #     manual = Help()
    #     manual.show(command)

    @staticmethod
    @image.command()
    def info(
        description: Annotated[
            Path, typer.Option(
                help='<directory> The description must be a directory '
                'containing a kiwi XML description and '
                'optional metadata files'
            )
        ],
        resolve_package_list: Annotated[
            Optional[bool], typer.Option(
                '--resolve-package-list',
                help='solve package dependencies and return a '
                'list of all packages including their attributes '
                'e.g. size, shasum, etc...'
            )
        ] = False,
        list_profiles: Annotated[
            Optional[bool], typer.Option(
                '--list-profiles',
                help='list profiles available for the selected/default type'
            )
        ] = False,
        print_kiwi_env: Annotated[
            Optional[bool], typer.Option(
                '--print-kiwi-env',
                help='list profiles available for the selected/default type'
            )
        ] = False,
        ignore_repos: Annotated[
            Optional[bool], typer.Option(
                '--ignore-repos',
                help='ignore all repos from the XML configuration'
            )
        ] = False,
        add_repo: Annotated[
            Optional[List[str]], typer.Option(
                help='<source,type,alias,priority> Add repository '
                'with given source, type, alias and priority. The '
                'option can be specified multiple times'
            )
        ] = [],
        print_xml: Annotated[
            Optional[bool], typer.Option(
                '--print-xml',
                help='print image description in XML'
            )
        ] = False,
        print_yaml: Annotated[
            Optional[bool], typer.Option(
                '--print-yaml',
                help='print image description in YAML'
            )
        ] = False,
        print_toml: Annotated[
            Optional[bool], typer.Option(
                '--print-toml',
                help='print image description in TOML'
            )
        ] = False
    ):
        """
        Provide information about the specified image description
        """
        Cli.subcommand_args['info'] = {
            '--description': f'{description}',
            '--resolve-package-list': resolve_package_list,
            '--list-profiles': list_profiles,
            '--print-kiwi-env': print_kiwi_env,
            '--ignore-repos': ignore_repos,
            '--add-repo': add_repo,
            '--print-xml': print_xml,
            '--print-yaml': print_yaml,
            '--print-toml': print_toml,
            'help': False
        }
        Cli.global_args['info'] = True
        Cli.global_args['command'] = 'info'
        Cli.global_args['image'] = True
        Cli.cli_ok = True

    @staticmethod
    @image.command()
    def resize(
        target_dir: Annotated[
            Path, typer.Option(
                help='<directory> The target directory '
                'to expect image build results'
            )
        ],
        size: Annotated[
            str, typer.Option(
                help='<size-unit> New size of the image. The value is either '
                'a size in bytes or can be specified with m=MB '
                'or g=GB. Example: 20g'
            )
        ],
        root: Annotated[
            Optional[Path], typer.Option(
                help='<directory> The path to the root directory, if not '
                'specified kiwi searches the root directory '
                'in build/image-root below the specified target '
                'directory'
            )
        ] = None
    ):
        """
        For disk based images, allow to resize the image to a new
        disk geometry. The additional space is free and not in use
        by the image. In order to make use of the additional free
        space a repartition process is required like it is provided
        by kiwi's oem boot code. Therefore the resize operation is
        useful for oem image builds most of the time
        """
        Cli.subcommand_args['resize'] = {
            '--target-dir': f'{target_dir}',
            '--size': size,
            '--root': root,
            'help': False
        }
        Cli.global_args['resize'] = True
        Cli.global_args['command'] = 'resize'
        Cli.global_args['image'] = True
        Cli.cli_ok = True

    @staticmethod
    @result.command()
    def list(
        target_dir: Annotated[
            Path, typer.Option(
                help='the target directory to expect image build results'
            )
        ]
    ):
        """
        List result information from a previously built image
        """
        Cli.subcommand_args['list'] = {
            '--target-dir': target_dir,
            'help': False
        }
        Cli.global_args['list'] = True
        Cli.global_args['command'] = 'list'
        Cli.global_args['result'] = True
        Cli.cli_ok = True

    @staticmethod
    @result.command()
    def bundle(
        target_dir: Annotated[
            Path, typer.Option(
                help='<directory> The target directory to '
                'expect image build results'
            )
        ],
        id: Annotated[
            str, typer.Option(
                help='<bundle_id> The bundle id. A free form text '
                'appended to the version information of the result '
                'image filename'
            )
        ],
        bundle_dir: Annotated[
            str, typer.Option(
                help='<directory> Directory to store the bundle results'
            )
        ],
        bundle_format: Annotated[
            Optional[str], typer.Option(
                help='<format> The bundle format to create the bundle. '
                'If provided this setting will overwrite an eventually '
                'provided bundle_format attribute from the main '
                'image description'
            )
        ] = None,
        zsync_source: Annotated[
            Optional[str], typer.Option(
                help='<download_location> Specify the download '
                'location from which the bundle file(s) can be '
                'fetched from. The information is effective if zsync '
                'is used to sync the bundle. The zsync control file '
                'is only created for those bundle files which are '
                'marked for compression because in a kiwi build '
                'only those are meaningful for a partial binary '
                'file download. It is expected that all files from a '
                'bundle are placed to the same download location'
            )
        ] = None,
        package_as_rpm: Annotated[
            Optional[bool], typer.Option(
                '--package-as-rpm',
                help='Take all result files and create an rpm package out of it'
            )
        ] = False
    ):
        """
        Create result bundle from the image build results in the
        specified target directory. Each result image will contain
        the specified bundle identifier as part of its filename.
        Uncompressed image files will also become xz compressed
        and a sha sum will be created from every result image.
        """
        Cli.subcommand_args['bundle'] = {
            '--target-dir': target_dir,
            '--id': id,
            '--bundle-dir': bundle_dir,
            '--bundle-format': bundle_format,
            '--zsync-source': zsync_source,
            '--package-as-rpm': package_as_rpm,
            'help': False
        }
        Cli.global_args['bundle'] = True
        Cli.global_args['command'] = 'bundle'
        Cli.global_args['result'] = True
        Cli.cli_ok = True

    @staticmethod
    @system.command()
    def build(
        description: Annotated[
            Path, typer.Option(
                help='<directory> The description must be a '
                'directory containing a kiwi XML description '
                'and optional metadata files'
            )
        ],
        target_dir: Annotated[
            Path, typer.Option(
                help='<directory> The target directory to '
                'store the system image file(s)'
            )
        ],
        allow_existing_root: Annotated[
            Optional[bool], typer.Option(
                '--allow-existing-root',
                help='Allow to use an existing root directory '
                'from an earlier build attempt. Use with caution '
                'this could cause an inconsistent root tree if the '
                'existing contents does not fit to the former '
                'image type setup'
            )
        ] = False,
        clear_cache: Annotated[
            Optional[bool], typer.Option(
                '--clear-cache',
                help='Delete repository cache for each of the '
                'used repositories before installing any package'
            )
        ] = False,
        ignore_repos: Annotated[
            Optional[bool], typer.Option(
                '--ignore-repos',
                help='Ignore all repos from the XML configuration'
            )
        ] = False,
        ignore_repos_used_for_build: Annotated[
            Optional[bool], typer.Option(
                '--ignore-repos-used-for-build',
                help='Ignore all repos from the XML configuration '
                'except the ones marked as imageonly'
            )
        ] = False,
        set_repo: Annotated[
            Optional[str], typer.Option(
                help='<source,type,alias,priority,imageinclude, '
                'package_gpgcheck,{signing_keys},components,distribution, '
                'repo_gpgcheck,repo_sourcetype> Overwrite the first XML '
                'listed repository source, type, alias, priority, '
                'imageinclude(true|false), package_gpgcheck(true|false), '
                'list of signing_keys enclosed in curly brackets delimited '
                'by a colon, component list for debian based repos as string '
                'delimited by a space, main distribution name for '
                'debian based repos, repo_gpgcheck(true|false) and '
                'repo_sourcetype(metalink|baseurl|mirrorlist)'
            )
        ] = None,
        set_repo_credentials: Annotated[
            Optional[str], typer.Option(
                help='<user:pass_or_filename> '
                'For repo sources of the form: uri://user:pass@location, '
                'set the user and password connected to the set-repo '
                'specification. If the provided value describes a '
                'filename in the filesystem, the first line of that '
                'file is read and used as credentials information.'
            )
        ] = None,
        add_repo: Annotated[
            Optional[List[str]], typer.Option(
                help='Same as --set-repo, but it adds the repo to the '
                'current list of repositories. The option can be specified '
                'multiple times'
            )
        ] = [],
        add_repo_credentials: Annotated[
            Optional[List[str]], typer.Option(
                help='Same as --set-repo-credentials, but The first '
                '--add-repo-credentials is connected with the first '
                '--add-repo specification and so on. The option can be '
                'specified multiple times'
            )
        ] = [],
        add_package: Annotated[
            Optional[List[str]], typer.Option(
                help='<name> Install the given package name '
                'The option can be specified multiple times'
            )
        ] = [],
        add_bootstrap_package: Annotated[
            Optional[List[str]], typer.Option(
                help='<name> Install the given package name as '
                'part of the early bootstrap process. The option '
                'can be specified multiple times'
            )
        ] = [],
        delete_package: Annotated[
            Optional[List[str]], typer.Option(
                help='<name> Delete the given package name '
                'The option can be specified multiple times'
            )
        ] = [],
        set_container_derived_from: Annotated[
            Optional[str], typer.Option(
                help='<uri> Overwrite the source location of the '
                'base container for the selected image type. '
                'The setting is only effective if the configured '
                'image type is setup with an initial derived_from reference'
            )
        ] = None,
        set_container_tag: Annotated[
            Optional[str], typer.Option(
                help='<name> Overwrite the container tag in the '
                'container configuration. The setting is only '
                'effective if the container configuraiton provides '
                'an initial tag value'
            )
        ] = None,
        add_container_label: Annotated[
            Optional[List[str]], typer.Option(
                help='<name=value> Add a container label in the '
                'container configuration metadata. The label with '
                'the provided key-value pair will be overwritten '
                'in case it was already defined in the XML description. '
                'The option can be specified multiple times'
            )
        ] = [],
        set_type_attr: Annotated[
            Optional[List[str]], typer.Option(
                help='<attribute=value> Overwrite/set the attribute '
                'with the provided value in the selected build type '
                'section. The option can be specified multiple times'
            )
        ] = [],
        set_release_version: Annotated[
            Optional[str], typer.Option(
                help='<version> Overwrite/set the release-version '
                'element in the selected build type preferences section'
            )
        ] = None,
        signing_key: Annotated[
            Optional[List[Path]], typer.Option(
                help='<key-file> Includes the given key-file as a trusted '
                'key for package manager validations. The option can be '
                'specified multiple times'
            )
        ] = [],
        ca_cert: Annotated[
            Optional[List[Path]], typer.Option(
                help='include additional CA certificate to import immediately '
                'after bootstrap and make available during the build process.'
            )
        ] = [],
        ca_target_distribution: Annotated[
            Optional[str], typer.Option(
                help='Specify target distribution for the import of '
                'certificates via the --ca-cert options(s) and/or the '
                'provided <certificates> from the image description. '
                'The selected distribution is used in KIWI to map the '
                'distribution specific CA storage path and update tool '
                'for the import process.'
            )
        ] = None,
    ):
        """
        Build a system image from the specified description. The
        build command combines the prepare and create commands.
        """
        Cli.subcommand_args['build'] = {
            '--description': f'{description}',
            '--target-dir': f'{target_dir}',
            '--allow-existing-root': allow_existing_root,
            '--clear-cache': clear_cache,
            '--ignore-repos': ignore_repos,
            '--ignore-repos-used-for-build': ignore_repos_used_for_build,
            '--set-repo': set_repo,
            '--set-repo-credentials': set_repo_credentials,
            '--add-repo': add_repo,
            '--add-repo-credentials': add_repo_credentials,
            '--add-package': add_package,
            '--add-bootstrap-package': add_bootstrap_package,
            '--delete-package': delete_package,
            '--set-container-derived-from': set_container_derived_from,
            '--set-container-tag': set_container_tag,
            '--add-container-label': add_container_label,
            '--set-type-attr': set_type_attr,
            '--set-release-version': set_release_version,
            '--signing-key': signing_key,
            '--ca-cert': ca_cert,
            '--ca-target-distribution': ca_target_distribution,
            'help': False
        }
        Cli.global_args['build'] = True
        Cli.global_args['command'] = 'build'
        Cli.global_args['system'] = True
        Cli.cli_ok = True

    @staticmethod
    @system.command()
    def prepare(
        description: Annotated[
            Path, typer.Option(
                help='<directory> The description must be a '
                'directory containing a kiwi XML description '
                'and optional metadata files'
            )
        ],
        root: Annotated[
            Path, typer.Option(
                help='<directory> The path to the new root '
                'directory of the system '
            )
        ],
        allow_existing_root: Annotated[
            Optional[bool], typer.Option(
                '--allow-existing-root',
                help='Allow to use an existing root directory '
                'from an earlier build attempt. Use with caution '
                'this could cause an inconsistent root tree if the '
                'existing contents does not fit to the former '
                'image type setup'
            )
        ] = False,
        clear_cache: Annotated[
            Optional[bool], typer.Option(
                '--clear-cache',
                help='Delete repository cache for each of the '
                'used repositories before installing any package'
            )
        ] = False,
        ignore_repos: Annotated[
            Optional[bool], typer.Option(
                '--ignore-repos',
                help='Ignore all repos from the XML configuration'
            )
        ] = False,
        ignore_repos_used_for_build: Annotated[
            Optional[bool], typer.Option(
                '--ignore-repos-used-for-build',
                help='Ignore all repos from the XML configuration '
                'except the ones marked as imageonly'
            )
        ] = False,
        set_repo: Annotated[
            Optional[str], typer.Option(
                help='<source,type,alias,priority,imageinclude, '
                'package_gpgcheck,{signing_keys},components,distribution, '
                'repo_gpgcheck,repo_sourcetype> Overwrite the first XML '
                'listed repository source, type, alias, priority, '
                'imageinclude(true|false), package_gpgcheck(true|false), '
                'list of signing_keys enclosed in curly brackets delimited '
                'by a colon, component list for debian based repos as string '
                'delimited by a space, main distribution name for '
                'debian based repos, repo_gpgcheck(true|false) and '
                'repo_sourcetype(metalink|baseurl|mirrorlist)'
            )
        ] = None,
        set_repo_credentials: Annotated[
            Optional[str], typer.Option(
                help='<user:pass_or_filename> '
                'For repo sources of the form: uri://user:pass@location, '
                'set the user and password connected to the set-repo '
                'specification. If the provided value describes a '
                'filename in the filesystem, the first line of that '
                'file is read and used as credentials information.'
            )
        ] = None,
        add_repo: Annotated[
            Optional[List[str]], typer.Option(
                help='Same as --set-repo, but it adds the repo to the '
                'current list of repositories. The option can be specified '
                'multiple times'
            )
        ] = [],
        add_repo_credentials: Annotated[
            Optional[List[str]], typer.Option(
                help='Same as --set-repo-credentials, but The first '
                '--add-repo-credentials is connected with the first '
                '--add-repo specification and so on. The option can be '
                'specified multiple times'
            )
        ] = [],
        add_package: Annotated[
            Optional[List[str]], typer.Option(
                help='<name> Install the given package name '
                'The option can be specified multiple times'
            )
        ] = [],
        add_bootstrap_package: Annotated[
            Optional[List[str]], typer.Option(
                help='<name> Install the given package name as '
                'part of the early bootstrap process. The option '
                'can be specified multiple times'
            )
        ] = [],
        delete_package: Annotated[
            Optional[List[str]], typer.Option(
                help='<name> Delete the given package name '
                'The option can be specified multiple times'
            )
        ] = [],
        set_container_derived_from: Annotated[
            Optional[str], typer.Option(
                help='<uri> Overwrite the source location of the '
                'base container for the selected image type. '
                'The setting is only effective if the configured '
                'image type is setup with an initial derived_from reference'
            )
        ] = None,
        set_container_tag: Annotated[
            Optional[str], typer.Option(
                help='<name> Overwrite the container tag in the '
                'container configuration. The setting is only '
                'effective if the container configuraiton provides '
                'an initial tag value'
            )
        ] = None,
        add_container_label: Annotated[
            Optional[List[str]], typer.Option(
                help='<name=value> Add a container label in the '
                'container configuration metadata. The label with '
                'the provided key-value pair will be overwritten '
                'in case it was already defined in the XML description. '
                'The option can be specified multiple times'
            )
        ] = [],
        set_type_attr: Annotated[
            Optional[List[str]], typer.Option(
                help='<attribute=value> Overwrite/set the attribute '
                'with the provided value in the selected build type '
                'section. The option can be specified multiple times'
            )
        ] = [],
        set_release_version: Annotated[
            Optional[str], typer.Option(
                help='<version> Overwrite/set the release-version '
                'element in the selected build type preferences section'
            )
        ] = None,
        signing_key: Annotated[
            Optional[List[Path]], typer.Option(
                help='<key-file> Includes the given key-file as a trusted '
                'key for package manager validations. The option can be '
                'specified multiple times'
            )
        ] = [],
        ca_cert: Annotated[
            Optional[List[Path]], typer.Option(
                help='include additional CA certificate to import immediately '
                'after bootstrap and make available during the build process.'
            )
        ] = [],
        ca_target_distribution: Annotated[
            Optional[str], typer.Option(
                help='Specify target distribution for the import of '
                'certificates via the --ca-cert options(s) and/or the '
                'provided <certificates> from the image description. '
                'The selected distribution is used in KIWI to map the '
                'distribution specific CA storage path and update tool '
                'for the import process.'
            )
        ] = None,
    ):
        """
        Prepare and install a new system root tree for chroot access.
        """
        Cli.subcommand_args['prepare'] = {
            '--description': f'{description}',
            '--root': f'{root}',
            '--allow-existing-root': allow_existing_root,
            '--clear-cache': clear_cache,
            '--ignore-repos': ignore_repos,
            '--ignore-repos-used-for-build': ignore_repos_used_for_build,
            '--set-repo': set_repo,
            '--set-repo-credentials': set_repo_credentials,
            '--add-repo': add_repo,
            '--add-repo-credentials': add_repo_credentials,
            '--add-package': add_package,
            '--add-bootstrap-package': add_bootstrap_package,
            '--delete-package': delete_package,
            '--set-container-derived-from': set_container_derived_from,
            '--set-container-tag': set_container_tag,
            '--add-container-label': add_container_label,
            '--set-type-attr': set_type_attr,
            '--set-release-version': set_release_version,
            '--signing-key': signing_key,
            '--ca-cert': ca_cert,
            '--ca-target-distribution': ca_target_distribution,
            'help': False
        }
        Cli.global_args['prepare'] = True
        Cli.global_args['command'] = 'prepare'
        Cli.global_args['system'] = True
        Cli.cli_ok = True

    @staticmethod
    @system.command()
    def update(
        root: Annotated[
            Path, typer.Option(
                help='<directory> The path to the root directory'
            )
        ],
        add_package: Annotated[
            Optional[List[str]], typer.Option(
                help='<name> Install the given package name '
                'The option can be specified multiple times'
            )
        ] = [],
        delete_package: Annotated[
            Optional[List[str]], typer.Option(
                help='<name> Delete the given package name '
                'The option can be specified multiple times'
            )
        ] = []
    ):
        """
        Update root system with latest repository updates
        and optionally allow to add or delete packages.
        """
        Cli.subcommand_args['update'] = {
            '--root': root,
            '--add-package': add_package,
            '--delete-package': delete_package
        }
        Cli.global_args['update'] = True
        Cli.global_args['command'] = 'update'
        Cli.global_args['system'] = True
        Cli.cli_ok = True

    @staticmethod
    @system.command()
    def create(
        root: Annotated[
            Path, typer.Option(
                help='<directory> The path to the root directory'
            )
        ],
        target_dir: Annotated[
            Path, typer.Option(
                help='<directory> The target directory to '
                'store the system image file(s)'
            )
        ],
        signing_key: Annotated[
            Optional[List[Path]], typer.Option(
                help='<key-file> Includes the given key-file as a trusted '
                'key for package manager validations. The option can be '
                'specified multiple times'
            )
        ] = [],
    ):
        """
        Create an image from the specified root directory.
        """
        Cli.subcommand_args['create'] = {
            '--root': root,
            '--target-dir': target_dir,
            '--signing-key': signing_key
        }
        Cli.global_args['create'] = True
        Cli.global_args['command'] = 'create'
        Cli.global_args['system'] = True
        Cli.cli_ok = True

    def get_servicename(self):
        """
        Extract service name from argument parse result

        :return: service name

        :rtype: str
        """
        if Cli.global_args.get('image') is True:
            return 'image'
        elif Cli.global_args.get('system') is True:
            return 'system'
        elif Cli.global_args.get('result') is True:
            return 'result'
        else:
            raise KiwiUnknownServiceName(
                'Unknown/Invalid Servicename'
            )

    def get_command(self):
        """
        Extract selected command name

        :return: command name
        :rtype: str
        """
        return Cli.global_args['command']

    def get_command_args(self, raise_if_no_command: bool = True) -> Dict:
        """
        Get argument dict for selected command
        including global options

        :return:
            Contains dictionary of command arguments

            .. code:: python

                {
                    '--some-option-name': 'value'
                }

        :rtype: dict
        """
        result = Cli.global_args
        command = self.get_command()
        if Cli.subcommand_args.get(command):
            result.update(
                Cli.subcommand_args.get(command) or {}
            )
        elif raise_if_no_command:
            raise KiwiCommandNotLoaded(
                f'{command} command not loaded'
            )
        return result

    def get_global_args(self):
        """
        Get argument dict for global arguments

        :return:
            Contains dictionary of global arguments

            .. code:: python

                {
                    '--some-global-option': 'value'
                }

        :rtype: dict
        """
        result = {}
        for arg, value in list(Cli.global_args.items()):
            if not arg == 'command':
                if arg == '--type' and value == 'vmx':
                    log.warning(
                        'vmx type is now a subset of oem, --type set to oem'
                    )
                    value = 'oem'
                if arg == '--shared-cache-dir' and value:
                    Defaults.set_shared_cache_location(value)
                if arg == '--temp-dir' and value:
                    Defaults.set_temp_location(value)
                if arg == '--target-arch' and value:
                    Defaults.set_platform_name(value)
                if arg == '--config' and value:  # pragma: no cover
                    Defaults.set_custom_runtime_config_file(value)
                result[arg] = value
        return result

    def load_plugin_cli(self) -> Dict[str, typer.Typer]:
        """
        Loads plugin command line interface

        The loading is based on the plugin entry point name
        and requires the presence of a Typer based cli.py.
        The implementation of cli.py in the plugin also
        requires to provide a dict named typers. The matching
        of an entry point to be a valid kiwi plugin requires
        the entry point group to be set to kiwi.tasks and
        the entry point value must container the _plugin
        substring.

        :return: list of typer.Typer instances

        :rtype: list
        """
        plugin_typers = {}
        for entry in self._get_module_entries():
            if '_plugin' in entry.value:
                module_name = entry.value.split('.')[0]
                plugin_entry = EntryPoint(
                    name='cli',
                    value=f'{module_name}.cli',
                    group='kiwi.tasks'
                )
                try:
                    plugin = plugin_entry.load()
                    plugin_typers.update(plugin.typers)
                except ModuleNotFoundError:
                    # plugin gets skipped if it does not provide
                    # a typer based cli
                    pass
                except Exception as issue:
                    raise KiwiLoadPluginError(
                        f'{plugin_entry}: {issue}'
                    )
        return plugin_typers

    def load_command(self):
        """
        Loads task class plugin according to service and command name

        :return: loaded task module

        :rtype: object
        """
        discovered_tasks = {}
        for entry in self._get_module_entries():
            discovered_tasks[entry.name] = entry.load()

        service = self.get_servicename()
        command = self.get_command()

        if not command:
            raise KiwiLoadCommandUndefined(
                'No command specified for {0} service'.format(service)
            )

        self.command_loaded = discovered_tasks.get(
            f'{service}_{command}'
        )
        if not self.command_loaded:
            prefix = 'usage:'
            discovered_tasks_for_service = ''
            for task in discovered_tasks:
                if task.startswith(service):
                    discovered_tasks_for_service += '{0} kiwi-ng {1}\n'.format(
                        prefix, task.replace('_', ' ')
                    )
                    prefix = '      '
            raise KiwiCommandNotLoaded(
                'Command "{0}" not found\n\n{1}'.format(
                    command, discovered_tasks_for_service
                )
            )
        return self.command_loaded

    def _get_module_entries(self) -> List[EntryPoint]:
        """
        Lookup module entries matching the kiwi.tasks entry group
        """
        entries: List[EntryPoint] = []
        if sys.version_info >= (3, 12):
            for entry in list(entry_points()):  # pragma: no cover
                if entry.group == 'kiwi.tasks':
                    entries.append(entry)
        else:  # pragma: no cover
            for entry in dict.get(entry_points(), 'kiwi.tasks') or {}:
                entries.append(entry)
        return entries
