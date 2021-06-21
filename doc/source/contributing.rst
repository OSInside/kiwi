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

The Basics
----------

The core appliance builder is developed in Python and follows the test
driven development rules.

If you want to implement a bigger feature, consider opening an issue on
GitHub first to discuss the changes. Or join the discussion in the
``#kiwi`` channel on `Riot.im <https://about.riot.im>`_.

Fork the upstream repository
----------------------------

1. On GitHub, navigate to: https://github.com/OSInside/kiwi

2. In the top-right corner of the page, click :command:`Fork`.

Create a local clone of the forked repository
---------------------------------------------

.. code:: shell-session

    $ git clone https://github.com/YOUR-USERNAME/kiwi

    $ git remote add upstream https://github.com/OSInside/kiwi.git

Install Required Operating System Packages
------------------------------------------

{kiwi} requires the following additional packages which are not provided by
:command:`pip`:

XML processing libraries
  `libxml2` and `libxslt` (for :mod:`lxml`)

Python header files, GCC compiler and glibc-devel header files
  Required for python modules that hooks into shared library context

Spell Checking library
  Provided by the `enchant` library

ShellCheck
  `ShellCheck <https://github.com/koalaman/shellcheck>`_ script linter.

ISO creation program
  One of ``xorriso`` (preferred) or ``genisoimage``.

LaTeX documentation build environment
  A full LaTeX installation is required to build the PDF documentation
  [#f1]_.

Host Requirements To Build Images
  A full set of tools needed to build images and provided by
  the `kiwi-systemdeps` package

The above mentioned system packages will be installed by calling the
`install_devel_packages.sh` helper script from the checked out Git
repository as follows:

.. code:: shell-session

   $ sudo helper/install_devel_packages.sh

.. note::

   The helper script checks for the package managers `zypper` and
   `dnf` and associates a distribution with it. If you use a
   distribution that does not use one of those package managers
   the script will not install any packages and exit with an
   error message. In this case we recommend to take a look at
   the package list encoded in the script and adapt to your
   distribution and package manager as needed.

Create a Python Virtual Development Environment
-----------------------------------------------

The following commands initializes and activates a development
environment for Python 3:

.. code:: shell-session

   $ tox -e devel
   $ source .tox/3/bin/activate

The commands above automatically creates the application script
called :command:`kiwi-ng`, which allows you to run {kiwi} from the
Python sources inside the virtual environment:

.. code:: shell-session

    $ kiwi-ng --help

.. warning::

   The virtualenv's `$PATH` will not be taken into account when calling
   {kiwi} via :command:`sudo`! Use the absolute path to the {kiwi} executable
   to run an actual build using your local changes:

   .. code:: shell-session

      $ sudo $PWD/.tox/3/bin/kiwi-ng system build ...

To leave the development mode, run:

.. code:: shell-session

    $ deactivate

To resume your work, :command:`cd` into your local Git repository and call:

.. code:: shell-session

    $ source .tox/3/bin/activate


Alternatively, you can launch single commands inside the virtualenv without
sourcing it directly:

.. code:: shell-session

   $ tox -e devel -- kiwi-ng --version


Running the Unit Tests
----------------------

We use :command:`tox` to run the unit tests. Tox sets up its own
virtualenvs inside the :file:`.tox` directory for multiple Python versions
and should thus **not** be invoked from inside your development virtualenv.

Before submitting your changes via a pull request, ensure that all tests
pass and that the code has the required test coverage via the command:

.. code:: shell-session

    $ tox

We also include `pytest-xdist` in the development virtualenv which allows
to run the unit tests in parallel. It is turned off by default but can be
enabled via:

.. code:: shell-session

    $ tox "-n NUMBER_OF_PROCESSES"

where you can insert an arbitrary number as `NUMBER_OF_PROCESSES` (or a
shell command like `$(nproc)`). Note that the double quotes around `-n
NUMBER_OF_PROCESSES` are required (otherwise :command:`tox` will consume
this command line flag instead of forwarding it to :command:`pytest`).

The previous call would run the unit tests for different Python versions,
check the source code for errors and build the documentation.

If you want to see the available targets, use the option `-l` to let
:command:`tox` print a list of them:

.. code:: shell-session

    $ tox -l

To only run a special target, use the `-e` option. The following
example runs the test cases for the Python 3.6 interpreter only:

.. code:: shell-session

    $ tox -e unit_py3_6


Create a Branch for each Feature or Bugfix
------------------------------------------

Code changes should be done in an extra Git branch. This allows for
creating GitHub pull requests in a clean way. See also: `Collaborating with
issues and pull requests
<https://help.github.com/en/categories/collaborating-with-issues-and-pull-requests>`_

.. code:: shell-session

    $ git checkout -b my-topic-branch

Make and commit your changes.

.. note::

    You can make multiple commits which is generally useful to
    give your changes a clear structure and to allow us to better
    review your work.

.. note::

    Your work is important and must be signed to ensure the integrity of
    the repository and the code. Thus we recommend to setup a signing key
    as documented in :ref:`Signing_Git_Patches`.

.. code:: shell-session

    $ git commit -S -a

Run the tests and code style checks. All of these are also performed by
`GitLab CI <https://gitlab.com/kiwi3>`_ when a pull request is created.

.. code:: shell-session

    $ tox

Once everything is done, push your local branch to your forked repository and
create a pull request into the upstream repository.

.. code:: shell-session

    $ git push origin my-topic-branch

Thank you much for contributing to {kiwi}. Your time and work effort is very
much appreciated!


Coding Style
------------

{kiwi} follows the general PEP8 guidelines with the following exceptions:

- We do not use free functions at all. Even utility functions must be part
  of a class, but should be either prefixed with the `@classmethod` or
  `@staticmethod` decorators (whichever is more appropriate).

- Do not set module and class level variables, put these into the classes'
  `__init__` method.

- The names of constants are not written in all capital letters.


Documentation
~~~~~~~~~~~~~

{kiwi} uses `Sphinx <https://www.sphinx-doc.org/en/master/>`_ for the API and
user documentation.

In order to build the HTML documentation call:

.. code:: shell-session

    tox -e doc

or to build the full documentation (including a PDF generated by LaTeX
[#f3]_):

.. code:: shell-session

    tox -e packagedoc


Document all your classes, methods, their parameters and their types using
the standard `reStructuredText
<https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_
syntax as supported by Sphinx, an example class is documented as follows:

.. code:: python

   class Example:
       """
       **Example class**

       :param str param: A parameter
       :param bool : Source file name to compress
       :param list supported_zipper: List of supported compression tools
       :attr Optional[str] attr: A class attribute
       """
       def __init__(self, param, param_w_default=False):
           self.attr = param if param_w_default else None

       def method(self, param):
           """
           A method that takes a parameter.

           :param list param: a parameter
           :return: whether param is very long
           :rtype: bool
           """
           return len(param) > 50


Try to stick to the following guidelines when documenting source code:

- Classes should be documented directly in their main docstring and not in
  `__init__`.

- Document **every** function parameter and every public attribute
  including their types.

- Only public methods should be documented, private methods don't have to,
  unless they are complex and it is not easy to grasp what they do (which
  should be avoided anyway).


Please also document any user-facing changes that you implementing
(e.g. adding a new build type) in the user documentation, which can be
found in `doc/source`. General documentation should be put into the
`working_with_kiwi/` subfolder, whereas documentation about more
specialized topics would belong into the `building/` subfolder.

Adhere to a line limit of 75 characters when writing the user facing
documentation [#f2]_.


Additional Information
----------------------

The following sections provides further information about the repository
integrity, version, package and documentation management.

.. _Signing_Git_Patches:

Signing Git Patches
~~~~~~~~~~~~~~~~~~~

To ensure the integrity of the repository and the code base, patches sent
for inclusion should be signed with a GPG key.

To prepare Git to sign commits, follow these instructions:

#. Create a key suitable for signing (it is not recommended to use
   existing keys to not mix it with your email environment):

   .. code:: shell-session

    $ gpg2 --expert --full-gen-key

#. Either choose a RSA key for signing (option `(4)`) or an ECC key for
   signing (option `(10)`). For a RSA key choose a key size of 4096 bits
   and for a ECC key choose Curve 25519 (option `(1)`). Enter a reasonable
   validity period (we recommend 2 to 5 years). Complete the key generation
   by entering your name and email address.


#. Add the key ID to your git configuration, by running the following
   :command:`git config` commands:

   .. code:: shell-session

      $ git config --local user.signingkey $YOUR_SIGN_KEY_ID
      $ git config --local commit.gpgSign true

   Omitting the flag `--local` will make these settings global for all
   repositories (they will be added to :file:`~/.gitconfig`). You can find
   your signkey's ID via:

   .. code:: shell-session

      $ gpg2 --list-keys --keyid-format long $YOUR_EMAIL
      pub   rsa4096/AABBCCDDEEFF0011 2019-04-26 [S] [expires: 2021-04-16]
      AAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBBBBBBBBB
      uid                 [ultimate] YOU <$YOUR_EMAIL>

   The key's ID in this case would be `AABBCCDDEEFF0011`. Note that your
   signkey will have only a `[S]` after the creation date, not a `[SC]`
   (then you are looking at your ordinary GPG key that can also encrypt).


Bumping the Version
~~~~~~~~~~~~~~~~~~~

The {kiwi} project follows the `Semantic Versioning <https://semver.org>`_
scheme. We use the :command:`bumpversion` tool for consistent versioning.

Follow these instructions to bump the major, minor, or patch part of the
{kiwi} version. Ensure that your repository is clean (i.e. no modified and
unknown files exist) beforehand running :command:`bumpversion`.

*  For backwards-compatible bug fixes:

   .. code:: shell-session

    $ bumpversion patch

*  For additional functionality in a backwards-compatible manner. When
   changed, the patch level is reset to zero:

   .. code:: shell-session

    $ bumpversion minor

*  For incompatible API changes. When changed, the patch and minor
   levels are reset to zero:

   .. code:: shell-session

    $ bumpversion major

Creating a RPM Package
~~~~~~~~~~~~~~~~~~~~~~

We provide a template for a RPM spec file in
:file:`package/python-kiwi-spec-template` alongside with a rpmlint
configuration file and an automatically updated
:file:`python-kiwi.changes`.

To create the necessary files to build a RPM package via `rpmbuild`, run:

.. code:: shell-session

   $ make build

The sources are collected in the :file:`dist/` directory. These can be
directly build it with :command:`rpmbuild`, :command:`fedpkg`, or submitted
to the Open Build Service using :command:`osc`.


.. [#f1] Sphinx requires a plethora of additional LaTeX
         packages. Unfortunately there is currently no comprehensive list
         available. On Ubuntu/Debian installing `texlive-latex-extra`
         should be sufficient. For Fedora, consult the package list
         from :file:`.gitlab-ci.yml`.

.. [#f2] Configure your editor to automatically break lines and/or reformat
         paragraphs. For Emacs you can use `M-x set-fill-column RET 75` and
         `M-x auto-fill-mode RET` for automatic filling of paragraphs in
         conjunction with `M-x fill-paragraph` (usually bound to `M-q`) to
         reformat a paragraph to adhere to the current column width. For
         editing reStructuredText we recommend `rst-mode` (built-in to
         Emacs since version `23.1`).
         Vim users can set the text width via `:tw 75` and then use the
         commands `gwip` or `gq`.

.. [#f3] Requires a full LaTeX installation.
