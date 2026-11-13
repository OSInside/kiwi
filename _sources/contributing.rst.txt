Contributing
============

.. note:: **Abstract**

   This document describes the development process of {kiwi}
   and how you can be part of it. This description applies
   to version |version|.

.. toctree::
   :maxdepth: 1

   contributing/kiwi_from_python
   contributing/kiwi_plugin_architecture
   contributing/scripts_testing
   contributing/schema_extensions.rst

The core appliance builder is developed in Python and follows the
test-driven development rules.

If you want to implement a bigger feature, consider opening an issue on
GitHub first to discuss the changes. Or, join the discussion in the
`#kiwi` channel on `Matrix <https://matrix.to/#/#kiwi:matrix.org>`_.

Fork the upstream repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. On GitHub, navigate to: https://github.com/OSInside/kiwi.

2. In the top-right corner of the page, click :command:`Fork`.

Create a local clone of the forked repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: shell-session

    $ git clone https://github.com/YOUR-USERNAME/kiwi

    $ git remote add upstream https://github.com/OSInside/kiwi.git

Install Required Operating System Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{kiwi} requires additional packages at runtime that are not
provided by `pip`. Those will be pulled in by installing
the following package:

* kiwi-systemdeps

The package is provided on the Open Build Service in the
`Virtualization:Appliances:Builder
<https://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__
project. For manual inspection of the packages
that are pulled in from the above `kiwi-systemdeps` package, please refer
to the `package/python-kiwi-spec-template` spec file from the
checked-out Git repository.

Create a Python Virtual Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following commands initialize and activate a development
environment for Python 3:

.. code:: shell-session

   $ poetry install --all-extras

.. note::

   To create the python virtual env for another version of
   Python, e.g. 3.11, call the following prior the poetry install
   ::

       $ poetry env use python3.11

The command above automatically creates the application script
called :command:`kiwi-ng`, which allows you to run {kiwi} from the
Python sources inside the virtual environment using Poetry:

.. code:: shell-session

    $ poetry run kiwi-ng --help

Running the Unit Tests
~~~~~~~~~~~~~~~~~~~~~~

Before submitting your changes via a pull request, ensure that all tests
pass and that the code has the required test coverage via the command:

.. code:: shell-session

    $ make check
    $ make test

Coding Style
~~~~~~~~~~~~

{kiwi} follows the general PEP8 guidelines.

Documentation
~~~~~~~~~~~~~

{kiwi} uses `Sphinx <https://www.sphinx-doc.org/en/master/>`_ for the
user documentation and man pages.

.. code:: shell-session

    $ make docs

Bumping the Version
~~~~~~~~~~~~~~~~~~~

The {kiwi} project follows the `Semantic Versioning <https://semver.org>`_
scheme. We use the :command:`bumpversion` tool for consistent versioning.

AI policy
~~~~~~~~~

{kiwi} has a policy of human-centric development. Only humans can be authors
and are ultimately responsible for the quality of their contributions.
That said, assisted development with "AI" tools (particularly contemporary
LLM-based tools) is permitted with the restriction that such usage is clearly
labeled with the `Assisted-by:` trailer in the pull request and commit message.
The format of the trailer is as such: `Assisted-by: <Tool>:<model-id>`.

Examples of such trailers:

=================  =======================================
Tool               Trailer
=================  =======================================
Claude             `Assisted-by: Claude:claude-opus-4-6`
Gemini             `Assisted-by: Gemini:gemini-2.5-pro`
GitHub Copilot     `Assisted-by: Copilot:gpt-4o`
ChatGPT            `Assisted-by: ChatGPT:gpt-4o`
=================  =======================================

The trailers are required for the following scenarios:

- AI wrote or generated code that ended up in the commit
- AI substantially modified or refactored existing code
- AI generated an implementation that the contributor then adapted

It is **not** required for the following scenarios:

- AI was used for **research only** - asking questions, understanding APIs,
  exploring approaches - but the human wrote all the code
- AI performed purely **mechanical tasks** like formatting, running
  commands, or committing

All submitted changes must be at least self-reviewed and all other
guidelines continue to apply (follow code style, pass tests, make tests
for new functionality, etc.)

Intentional obfuscation of AI tooling usage is grounds for rejection
and may result in being blocked from future contributions.

Creating an RPM Package
~~~~~~~~~~~~~~~~~~~~~~~

We provide a template for an RPM spec file in
:file:`package/python-kiwi-spec-template` alongside a `rpmlint`
configuration file and an automatically updated
:file:`python-kiwi.changes`.

To create the necessary files to build an RPM package via `rpmbuild`, run:

.. code:: shell-session

   $ make build

The sources are collected in the :file:`dist/` directory. These can be
directly built with :command:`rpmbuild`, :command:`fedpkg`, or submitted
to the Open Build Service using :command:`osc`.
