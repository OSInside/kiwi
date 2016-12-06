Development and Contributing
============================

.. hint:: **Abstract**

   This document describes the development process of KIWI.
   This description applies for version |version|.

The core appliance builder is developed in Python and follows the test
driven development rules.

Runtime Requirements
---------------------

KIWI requires the following Python modules to run:

* :mod:`lxml`
* :mod:`docopt`
* :mod:`xattr`

Development Requirements
-------------------------

The Python project uses :command:`pyvenv` to setup a development environment
for the desired Python version. The script :command:`pyvenv` is already
installed when using Python 3.3 and higher (see
https://docs.python.org/3.3/whatsnew/3.3.html#pep-405-virtual-environments
for details). For Python 2.7 use :command:`virtualenv`.

However, for setting up a Python virtual development environment the
following additional include, header files and compilers are required
in order to allow for compiling the C parts of the runtime required
Python modules listed above:

* XML processing with libxml2 and libxslt (for :mod:`lxml`)
* Foreign function interface library (libffi48)
* Python header files (for :mod:`xattr`)
* GCC compiler and glibc-devel header files

The required components can be installed with the following command:

.. code:: bash

    $ zypper in python3-devel libxml2-devel libxslt-devel libffi48-devel glibc-devel gcc

.. note::

    The command above is only valid for SUSE systems.
    Package names and install command might be different
    on other systems.

For development, KIWI also takes the following additional
Python modules from :ghkiwi:`.virtualenv.dev-requirements.txt`
into account.

Contributing
------------

The following procedure describes how to create a Python3 virtual
development environment:

1. Create the virtual environment:

   .. code:: bash

    $ python3 -m venv .env3

2. Activate the virtual environment:

   .. code:: bash

    $ source .env3/bin/activate

3. Install KIWI requirements inside the virtual environment:

   .. code:: bash

    $ pip3.4 install -r .virtualenv.dev-requirements.txt

4. Install KIWI in "development mode":

   .. code:: bash

     $ ./setup.py develop

Once the development environment is activated and initialized with the
project required Python modules, you are ready to work.

The :command:`develop` target of the :command:`setup.py` script
automatically creates the application entry point called :command:`kiwi-ng`,
which allows to simply call the application from the current code base:

.. code:: bash

    $ kiwi-ng --help

In order to leave the development mode just call:

.. code:: bash

    $ deactivate

To resume your work, change into your local Git repository and recall:

.. code:: bash

    $ source .env3/bin/activate

If the version has changed by :command:`bumpversion`, this
causes the current entry point to become invalid. Reconstruct the
entry point after a version change by recalling:

.. code:: bash

    $ ./setup.py develop

Running Test Cases
~~~~~~~~~~~~~~~~~~

For running test cases, the preferred method is to use Tox. The Tox
execution environment can be used to run any kind of target, tests are
just one, documentation is another one. Refer to :file:`tox.ini` for more
details.

.. code:: bash

    $ tox

The previous call would run :command:`tox` for different Python versions,
checks the source code for errors, and builds the documentation.

If you want to see the target, use the option `-l` to print a list:

.. code:: bash

    $ tox -l

To only run a special target, use the `-e` option. The following
example runs the test cases for the 3.4 interpreter only:

.. code:: bash

    $ tox -e 3.4

Working with Branches
~~~~~~~~~~~~~~~~~~~~~

Code changes should be done in an extra git branch of the origin or
a forked git repository. This allows for creating github pull requests
in a clean way. Also See `Github Issues and Pull Requests <https://help.github.com/categories/collaborating-on-projects-using-issues-and-pull-requests>`__

Signing Git Patches
~~~~~~~~~~~~~~~~~~~

With ssh keys being widely available and the increasing compute power
available to many people refactoring of SSH keys is in the range of
possibilities. Therefore SSH keys as used by GitHub as a
"login/authentication" mechanism no longer provide the security they
once did. In an effort to ensure the integrity of the repository and
the code base patches sent for inclusion must be GPG signed.

To prepare Git to sign commits, follow these one-time instructions:

1. Create a key suitable for signing (its not recommended to use
   existing keys to not mix it up with your email environment etc):

   .. code:: bash

    $ gpg --gen-key

2. Choose a DSA key (3) with a key size of 2048 bits (default) and a
   validation of 3 years (3y). Enter your name/email and GPG will
   generate a DSA key for you.

   You can also choose to use an empty passphrase, despite GPG's warning,
   because you are only going to sign your public git commits with it and
   don't need it for protecting any of your secrets. That might ease later
   use if you are not using an :command:`gpg-agent` that caches your passphrase
   between multiple signed Git commits.

3. Add the key ID to your git config

   In above case, the ID is 11223344 so you add it to either your global
   :file:`~/.gitconfig` or even better to your :file:`.git/config`
   inside your repo:

   .. code:: ini

    [user]
    name = Joe Developer
    email = developer@foo.bar
    signingkey = 11223344

Once you have done the previous steps, use the following command to sign
your commit:

.. code:: bash

    $ git commit -S -a

The signatures created by this can later be verified using the
following command:

.. code:: bash

  $ git log --show-signature


Raising Versions
----------------

The KIWI project follows the `Semantic Versioning <http://semver.org>`__
method. To make it easier to follow this method, :command:`bumpversion` is
used as a tool.

Follow these instructions to raise the major, minor, or patch part of a
version:

*  For backwards-compatible bug fixes:

   .. code:: bash

    $ bumpversion patch

*  For additional functionality in a backwards-compatible manner. When
   changed, the patch level is set back to zero:

   .. code:: bash

    $ bumpversion minor

*  For incompatible API changes. When changed, the patch and minor
   levels are set back to zero:

   .. code:: bash

    $ bumpversion major


Creating a Package
------------------

The creation of RPM package sources has to be done by calling the
following make target:

.. code:: bash

   $ make build

The sources are collected below the :file:`dist/` directory. In there you
will find all required files to submit a package to the Open Build
Service or just build it with :command:`rpmbuild`.


Building Documentation
----------------------

The documentation is implemented using Sphinx with the ReST markup. In
order to build the documentation just call:

.. code:: bash

    tox -e doc

Whenever a change in the documentation is pushed to the git, it will be
automatically updated via :command:`travis-sphinx` and is available at:

http://suse.github.io/kiwi
