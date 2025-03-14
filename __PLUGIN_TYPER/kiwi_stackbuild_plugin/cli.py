import typer

from typing import (
    Annotated, Optional
)

# Filename must be cli.py and typers variable must be
# provided for kiwi plugins
typers = {
    'stackbuild': typer.Typer(
        add_completion=False
    ),
    'stash': typer.Typer(
        add_completion=False
    )
}

system_stackbuild = typers['stackbuild']
system_stash = typers['stash']

@system_stackbuild.callback(
    help='Build an image based on a given stash container root. '
    'If no KIWI description is provided along with the command, '
    'stackbuild rebuilds the image from the stash container. '
    'If a KIWI description is provided, this description takes '
    'over precedence and a new image from this description based '
    'on the given stash container root will be built.',
    invoke_without_command=True,
    subcommand_metavar=''
)
def stackbuild(
    ctx: typer.Context,
    some: Annotated[
        Optional[str], typer.Option(
            help='some'
        )
    ] = 'some'
):
    Cli=ctx.obj
    Cli.subcommand_args['stackbuild'] = {
        'some': some,
        'help': False
    }
    Cli.global_args['command'] = 'stackbuild'
    Cli.global_args['system'] = True
    Cli.cli_ok = True

@system_stash.callback(
    help='Create a container from the given root directory',
    invoke_without_command=True,
    subcommand_metavar=''
)
def stash(
    ctx: typer.Context,
    some: Annotated[
        Optional[str], typer.Option(
            help='some'
        )
    ] = 'some'
):
    Cli=ctx.obj
    Cli.subcommand_args['stash'] = {
        'some': some,
        'help': False
    }
    Cli.global_args['command'] = 'stash'
    Cli.global_args['system'] = True
    Cli.cli_ok = True
