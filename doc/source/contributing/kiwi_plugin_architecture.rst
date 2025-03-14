Plugin Architecture
===================

Each command provided by {kiwi} is written as a task plugin under the
**kiwi.tasks** namespace. As a developer, you can extend the {kiwi}
system command space with custom task plugins, following the conventions
below.

Naming conventions
------------------

Task plugin file name
  The file name of a task plugin must follow the pattern
  :file:`system_<command>.py`. This allows you to invoke the task
  with :command:`kiwi-ng system command ...`

Task plugin option handling
  {kiwi} uses the typer module to handle options. Each task plugin
  must use typer to allow option handling. The typer definition
  must be provided in a file named :file:`cli.py` and must live in the
  toplevel of the plugin python namespace.

Task plugin class
  The implementation of the plugin must be a class that matches the naming
  convention :class:`System<Command>Task`. The class must inherit from the
  :class:`CliTask` base class. On the plugin startup, {kiwi} expects an
  implementation of the :file:`process` method.

Task plugin entry point
  Registration of the plugin must be done in :file:`pyproject.toml`
  using the `tool.poetry.plugins` concept.

  .. code::

      [tool.poetry]
      name = "kiwi_plugin"

      packages = [
          { include = "kiwi_plugin"},
      ]

      [tool.poetry.plugins]
      [tool.poetry.plugins."kiwi.tasks"]
      system_<command> = "kiwi_<pluginname>_plugin.tasks.system_<command>"

Example plugin
--------------

.. note::

   The following example assumes an existing Python project
   which was set up using poetry and pyproject.toml.

1. Assuming the project namespace is **kiwi_relax_plugin**, create the task
   plugin directory :file:`kiwi_relax_plugin/tasks`.

2. Create the entry point in :command:`pyproject.toml`.

   Assuming we want to create the system command **justdoit**, this is
   the following entry point definition in :file:`pyproject.toml`:

   .. code:: toml

      [tool.poetry]
      name = "kiwi_relax_plugin"

      packages = [
          { include = "kiwi_relax_plugin"},
      ]

      [tool.poetry.plugins]
      [tool.poetry.plugins."kiwi.tasks"]
      system_justdoit = "kiwi_relax_plugin.tasks.system_justdoit"

3. Create the typer cli interface in the file
   :file:`kiwi_relax_plugin/cli.py` with the following
   content:

   .. code:: python

       import typer
       from typing import Annotated

       # typers variable must be provided for kiwi plugins
       typers = {
           'justdoit': typer.Typer(add_completion=False)
       }

       system = typers['justdoit']

       @system.callback(
           help='What is it good for'
           invoke_without_command=True,
           subcommand_metavar=''
       )
       def justdoit(
           ctx: typer.Context,
           now: Annotated[str, typer.Option(help='For --now option')]
       ):
           Cli=ctx.obj
           Cli.subcommand_args['justdoit'] = {
               '--now': now,
               'help': False
           }
           Cli.global_args['command'] = 'justdoit'
           Cli.global_args['system'] = True
           Cli.cli_ok = True

4. Create the plugin code in the file
   :file:`kiwi_relax_plugin/tasks/system_justdoit.py` with the following
   content:

   .. code:: python

       # These imports requires kiwi to be part of your environment
       # It can be either installed from pip into a virtual development
       # environment or from the distribution package manager.
       from kiwi.tasks.base import CliTask
       from kiwi.help import Help

       class SystemJustdoitTask(CliTask):
           def process(self):
               self.manual = Help()
               if self.command_args.get('help') is True:
                   # The following will invoke man to show the man page
                   # for the requested command. Thus, for the call to
                   # succeed, a man page needs to be written and
                   # installed by the plugin.
                   return self.manual.show('kiwi::relax::justdoit')

               if self.command_args.get('--now'):
                   print(
                       'https://genius.com/Frankie-goes-to-hollywood-relax-lyrics'
                   )

5. Test the plugin

   .. code:: bash

       $ poetry run kiwi-ng system justdoit --now
