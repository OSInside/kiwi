Development and Contributing
============================

.. hint:: **Abstract**

   This document describes the development process of KIWI
   and how you can be part of it. This description applies
   to version |version|.

.. toctree::
   :maxdepth: 1

   development/kiwi_from_python
   development/api/kiwi
   development/schema
   development/schema_extensions.rst

The core appliance builder is developed in Python and follows the test
driven development rules.

If you want to implement a bigger feature, consider opening an issue on
GitHub first to discuss the changes. Or join the discussion in the
``#kiwi`` channel on `Riot.im <https://riot.im/>`_.

Fork the upstream KIWI repository
---------------------------------

1. On GitHub, navigate to: https://github.com/SUSE/kiwi

2. In the top-right corner of the page, click :command:`Fork`.

Create a local clone of the forked KIWI repository
--------------------------------------------------

.. code:: shell-session

    $ git clone https://github.com/YOUR-USERNAME/kiwi

    $ git remote add upstream https://github.com/SUSE/kiwi.git

Install Required Operating System Packages
------------------------------------------

KIWI requires the following additional packages which are not provided by
:command:`pip`:

* XML processing libraries: `libxml2` and `libxslt` (for :mod:`lxml`)
* Python header files (for :mod:`xattr`), usually provided by a package
  called `python-devel` or `python3-devel`
* The `enchant` spell checking library
* gcc compiler and glibc-devel header files
* The `ShellCheck <https://github.com/koalaman/shellcheck>`_ script
  linter.
* A manipulation program for ISO images, either: ``xorriso`` (preferred) or
  ``genisoimage``.

A full LaTeX installation is required to build the PDF documentation
[#f1]_.

On SUSE based systems run:

.. code:: shell-session

   $ zypper install --no-recommends \
         python3-devel libxml2-devel libxslt-devel glibc-devel gcc \
         trang xorriso \
         texlive-fncychap texlive-wrapfig texlive-capt-of \
         texlive-latexmk texlive-cmap texlive-babel-english \
         texlive-times texlive-titlesec texlive-tabulary texlive-framed \
         texlive-float texlive-upquote texlive-parskip texlive-needspace \
         texlive-makeindex-bin texlive-collection-fontsrecommended \
         texlive-psnfss

On Fedora the following commands should install the required packages:

.. code:: shell-session

   $ dnf install python3 python3-devel 'python3dist(pip)' \
      'python3dist(tox)' make gcc which xz xorriso libxml2-devel \
      libxslt-devel enchant genisoimage ShellCheck
   $ # LaTeX packages
   $ dnf install latexmk texlive-cmap texlive-metafont texlive-ec \
      texlive-babel-english texlive-fncychap texlive-fancyhdr \
      texlive-titlesec texlive-tabulary texlive-framed texlive-wrapfig \
      texlive-parskip texlive-upquote texlive-capt-of texlive-needspace \
      texlive-makeindex texlive-times texlive-helvetic texlive-courier \
      texlive-gsftopk texlive-updmap-map texlive-dvips


Create a Python Virtual Development Environment
-----------------------------------------------

We recommend to setup a Python virtualenv for development. For Python 3
:command:`python3 -m venv` is used, as it is bundled with Python itself
(see https://docs.python.org/3/library/venv.html for details). For Python
2.7, use :command:`virtualenv`, which is provided via :command:`pip` or as
an extra package by your favorite Linux distribution.

The following commands initializes a development environment for Python 3:

.. code:: shell-session

   $ python3 -m venv .env3
   $ source .env3/bin/activate
   $ pip install -r .virtualenv.dev-requirements.txt
   $ python3 setup.py develop

The :command:`develop` target of the :command:`setup.py` script
automatically creates the application entry point called
:command:`kiwi-ng-3`, which allows you to call the your modified version of
KIWI from inside the virtual environment:

.. code:: shell-session

    $ kiwi-ng-3 --help

.. warning::

   The virtualenv's `$PATH` will not be taken into account when calling
   KIWI via :command:`sudo`! Use the absolute path to the KIWI executable
   to run an actual build using your local changes:

   .. code:: shell-session

      $ sudo $PWD/.env3/bin/kiwi-ng-3 system build ...


In order to leave the development mode call:

.. code:: shell-session

    $ deactivate

To resume your work, :command:`cd` into your local Git repository and call:

.. code:: shell-session

    $ source .env3/bin/activate


Running the Unit Tests
----------------------

We use :command:`tox` to run the unit tests. Tox sets up its own
virtualenvs inside the :file:`.tox` directory for multiple Python versions and should
thus **not** be invoked from inside your development virtualenv.

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
    check
    unit_py3_7
    unit_py3_6
    unit_py3_4
    unit_py2_7
    packagedoc

To only run a special target, use the `-e` option. The following
example runs the test cases for the Python 3.7 interpreter only:

.. code:: shell-session

    $ tox -e unit_py3_7

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

Run the tests and code style checks. All of these are also performed by the
`Travis CI <https://travis-ci.com/SUSE/kiwi>`_ and `GitLab CI
<https://gitlab.com/schaefi/kiwi-ci/pipelines>`_ integration test systems
when a pull request is created.

.. code:: shell-session

    $ tox

Once everything is done, push your local branch to your forked repository and
create a pull request into the upstream repository.

.. code:: shell-session

    $ git push origin my-topic-branch

Thank you much for contributing to KIWI. Your time and work effort is very
much appreciated!


Coding Style
------------

KIWI follows the general PEP8 guidelines with the following exceptions:

- We do not use free functions at all. Even utility functions must be part
  of a class, but should be either prefixed with the `@classmethod` or
  `@staticmethod` decorators (whichever is more appropriate).

- Do not set module and class level variables, put these into the classes'
  `__init__` method.

- The names of constants are not written in all capital letters.

- We do not use type hints (yet) as the current code base needs to maintain Python
  2 compatibility.


Documentation
~~~~~~~~~~~~~

KIWI uses `Sphinx <https://www.sphinx-doc.org/en/master/>`_ for the API and
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

   class Example(object):
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

The KIWI project follows the `Semantic Versioning <https://semver.org>`_
scheme. We use the :command:`bumpversion` tool for consistent versioning.

Follow these instructions to bump the major, minor, or patch part of the
KIWI version. Ensure that your repository is clean (i.e. no modified and
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
