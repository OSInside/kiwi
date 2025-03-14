import typer

from typing import (
    Annotated, Optional
)

# Filename must be cli.py and typers variable must be
# provided for kiwi plugins
typers = {
    'boxbuild': typer.Typer(
        add_completion=False
    )
}

system = typers['boxbuild']

@system.command(
    context_settings={
        'allow_extra_args': True,
        'ignore_unknown_options': True
    }
)
def kiwi(
    ctx: typer.Context,
):
    """
    Specify kiwi system build options
    """
    Cli=ctx.obj
    option = None
    for kiwi_arg in ctx.args:
        if kiwi_arg.startswith('-'):
            Cli.subcommand_args['boxbuild'][kiwi_arg] = True
        elif option:
            Cli.subcommand_args['boxbuild'][option] = kiwi_arg
        option = kiwi_arg
    Cli.global_args['command'] = 'boxbuild'
    Cli.global_args['system'] = True
    Cli.cli_ok = True

@system.callback(
    help='build a system image in a self contained virtual machine',
    subcommand_metavar='kiwi [OPTIONS]'
)
def boxbuild(
    ctx: typer.Context,
    some: Annotated[
        Optional[str], typer.Option(
            help='some'
        )
    ] = 'some'
):
    Cli=ctx.obj
    Cli.subcommand_args['boxbuild'] = {
        'some': some,
        'help': False
    }
