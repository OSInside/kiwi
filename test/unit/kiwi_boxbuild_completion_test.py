import re
import yaml
import click
import typer.main

from kiwi.cli import Cli
from kiwi.defaults import Defaults

COMPLETION_FILE = '../../tools/kiwi-boxbuild/completion/kiwi-boxbuild'


class TestKiwiBoxbuildCompletion:
    """
    The bash completion of kiwi-boxbuild provides the box names
    and the options of the kiwi-ng system build command, which
    is called in the box. Check that both match kiwi, such that
    they do not get out of sync
    """

    def setup_method(self, cls):
        with open(COMPLETION_FILE) as completion:
            self.completion = completion.read()

    def _get_list(self, variable):
        match = re.search(
            rf'^{variable}="([^"]*)"', self.completion, re.MULTILINE
        )
        assert match, f'{variable} not found in {COMPLETION_FILE}'
        return sorted(match.group(1).split())

    def test_build_options(self):
        system = typer.main.get_command(Cli.system)
        build = system.get_command(click.Context(system), 'build')
        value_options = []
        flag_options = []
        for param in build.params:
            for option in param.opts:
                if option.startswith('--'):
                    if param.is_flag:
                        flag_options.append(option)
                    else:
                        value_options.append(option)
        assert self._get_list('_kiwi_boxbuild_build_value_options') == sorted(
            value_options
        )
        assert self._get_list('_kiwi_boxbuild_build_flag_options') == sorted(
            flag_options
        )

    def test_boxes(self):
        with open(
            Defaults.project_file('config/kiwi_boxed_plugin.yml')
        ) as config:
            boxes = yaml.safe_load(config)['box']
        assert self._get_list('_kiwi_boxbuild_boxes') == sorted(
            box['name'] for box in boxes
        )
