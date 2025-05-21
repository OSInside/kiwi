Plugin Architecture
===================

Each command provided by {kiwi} is written as a task plugin under the
**kiwi.tasks** namespace. As a developer, you can extend {kiwi} with custom task
plugins, following the conventions below.

Naming conventions
------------------

Task plugin file name
  The file name of a task plugin must follow the pattern
  :file:`<service>_<command>.py`. This allows you to invoke the task
  with :command:`kiwi-ng service command ...`

Task plugin option handling
  {kiwi} uses the docopt module to handle options. Each task plugin
  must use docopt to allow option handling.

Task plugin class
  The implementation of the plugin must be a class that matches the naming
  convention :class:`<Service><Command>Task`. The class must inherit from the
  :class:`CliTask` base class. On the plugin startup, {kiwi} expects an
  implementation of the :file:`process` method.

Task plugin entry point
  Registration of the plugin must be done in :file:`pyproject.toml`
  using the ``tool.poetry.plugins`` concept.

  .. code:: python

      [tool.poetry]
      name = "kiwi_plugin"

      packages = [
          { include = "kiwi_plugin"},
      ]

      [tool.poetry.plugins]
      [tool.poetry.plugins."kiwi.tasks"]
      service_command = "kiwi_plugin.tasks.service_command"

Example plugin
--------------

.. note::

   The following example assumes an existing Python project
   which was set up using poetry and pyproject.toml.

1. Assuming the project namespace is **kiwi_relax_plugin**, create the task
   plugin directory :file:`kiwi_relax_plugin/tasks`

2. Create the entry point in :command:`pyproject.toml`.

   Assuming we want to create the service named **relax** that has
   the command **justdoit**, this is the required plugin
   definition in :file:`pyproject.toml`:

   .. code:: python

      [tool.poetry]
      name = "kiwi_relax_plugin"

      packages = [
          { include = "kiwi_relax_plugin"},
      ]

      [tool.poetry.plugins]
      [tool.poetry.plugins."kiwi.tasks"]
      relax_justdoit = "kiwi_relax_plugin.tasks.relax_justdoit"

3. Create the plugin code in the file
   :file:`kiwi_relax_plugin/tasks/relax_justdoit.py` with the following
   content:

   .. code:: python

       """
       usage: kiwi-ng relax justdoit -h | --help
              kiwi-ng relax justdoit --now
       
       commands:
           justdoit
               time to relax

       options:
           --now
               right now. For more details about docopt
               see: http://docopt.org
       """
       # These imports requires kiwi to be part of your environment
       # It can be either installed from pip into a virtual development
       # environment or from the distribution package manager
       from kiwi.tasks.base import CliTask
       from kiwi.help import Help

       class RelaxJustdoitTask(CliTask):
           def process(self):
               self.manual = Help()
               if self.command_args.get('help') is True:
                   # The following will invoke man to show the man page
                   # for the requested command. Thus for the call to
                   # succeed a manual page needs to be written and
                   # installed by the plugin
                   return self.manual.show('kiwi::relax::justdoit')

               print(
                   'https://genius.com/Frankie-goes-to-hollywood-relax-lyrics'
               )

4. Test the plugin

   .. code:: bash

       $ poetry run kiwi-ng relax justdoit --now
