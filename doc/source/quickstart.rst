KIWI Development Quickstart
===========================

.. topic:: Abstract

   This document describes the development process of KIWI,
   an OS appliance builder.
   This description applies for version |version|.


Installation
------------

Packages for the new KIWI version are provided at the `openSUSE
buildservice <http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__.

Add the repository with :command:`zypper ar` (see following code) and replace
the distribution placeholder. The best approach is to click on the
desired distribution from the buildservice link above and there follow
the **Go to download repository** link.

.. code:: bash

    $ sudo zypper ar -f \
        http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST>
    $ sudo zypper in python3-kiwi


Compatibility
-------------

The legacy KIWI version can be installed and used together with the next
generation KIWI.

.. note:: Automatic Link Creation for :command:`kiwi` Command

   Note the python3-kiwi package uses the alternatives mechanism to
   setup a symbolic link named :command:`kiwi` to the real executable
   named :command:`kiwi-ng`. If the link target :file:`/usr/bin/kiwi`
   already exists on your system, the alternative setup will skip the
   creation of the link target because it already exists.

From an appliance description perspective, both KIWI versions are fully
compatible. Users can build their appliances with both versions and the
same appliance description. If the appliance description uses features
the next generation KIWI does not provide, the build will fail with an
exception early. If the appliance description uses next generation
features like the selection of the initrd system, it's not possible to
build that with the legacy KIWI, unless the appliance description
properly encapsulates the differences into a profile.

The next generation KIWI also provides the `--compat` option and
the :command:`kiwicompat` tool to be able to use the same commandline
as provided with the legacy KIWI version.


Contributing
------------

The core appliance builder is developed in Python and follows the test
driven development rules. The XML, schema, and stylesheets are taken
from the old version of KIWI. Also the entire boot code (written in
bash) is taken from the old KIWI codebase.

The Python project uses :command:`pyvenv` to setup a development environment
for the desired Python version. The script :command:`pyvenv` is already
installed when using Python 3.3 and higher (see
https://docs.python.org/3.3/whatsnew/3.3.html#pep-405-virtual-environments
for details).

The following procedure describes how to create such an environment:

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

You're done!

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

To resume your work, change into your local Git repository and run
:command:`source .env3/bin/activate` again. Skip step 3 and 4 as the
requirements are already installed.

Running Test Cases
~~~~~~~~~~~~~~~~~~

For running test cases, the preferred method is to use Tox. The Tox
execution environment can be used to run any kind of target, tests are
just one, documentation is another one. Refer to tox.ini for more
details

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

Signing Git Patches
~~~~~~~~~~~~~~~~~~~

With ssh keys being widely available and the increasing compute power
available to many people refactoring of SSH keys is in the range of
possibilities. Therefore SSH keys as used by GitHub as a
"login/authentication" mechanism no longer provide the security they
once did. See `Github SSH keys
<https://cryptosense.com/batch-gcding-github-ssh-keys>`__ and
`Github Users keys <https://blog.benjojo.co.uk/post/auditing-github-users-keys>`__ as
reference. In an effort to ensure the integrity of the repository and
the code base patches sent for inclusion must be GPG signed.

To prepare Git to sign commits, follow these one-time instructions:

1. Create a key suitable for signing (its not recommended to use
   existing keys to not mix it up with your email environment etc):

   .. code:: bash

    $ gpg --gen-key

2. Choose a DSA key (3) with a keysize of 2048 bits (default) and a
   validation of 3 years (3y). Enter your name/email and gpg will
   generate a DSA key for you.

   You can also choose to use an empty passphrase, despite GPG's warning,
   because you are only going to sign your public git commits with it and
   dont need it for protecting any of your secrets. That might ease later
   use if you are not using an gpg-agent that caches your passphrase
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
automatically updated via travis-sphinx and is available at

http://suse.github.io/kiwi



Using KIWI NG from Build Service
---------------------------------

The next generation KIWI is fully integrated with the buildservice. As
an example you can find the integration testing system in the
buildservice project `Virtualization:Appliances:Images` at:

https://build.opensuse.org

In order to use the next generation KIWI to build an appliance in the
buildservice it is only required to add the Builder project as
repository to the KIWI XML configuration like in the following example:

.. code:: xml

 <repository type="rpm-md" alias="kiwi-next-generation">
    <source path="obs://Virtualization:Appliances:Builder/SLE_12_SP1"/>
 </repository>

The Builder project configuration in the buildservice is setup to prefer
the next generation KIWI over the legacy version. Thus adding the
Builder repository inherits this project setup and activates building
with the next generation KIWI.


Example Appliance Descriptions
------------------------------

For use with the next generation KIWI there is also a GitHub project
hosting example appliance descriptions. Users who need an example to
start with should checkout the project as follows:

.. code:: bash

    $ git clone https://github.com/SUSE/kiwi-descriptions

Example Image Build on Host System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install python3-kiwi as explained above and build as follows:

.. code:: bash

    $ sudo kiwi-ng --type vmx system build \
        --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
        --target-dir /tmp/myimage

Find the image with the suffix :file:`.raw` below :file:`/tmp/myimage`.

Example Image Build in Container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install `dice <https://github.com/SUSE/dice>`__ and build as follows:

.. code:: bash

    $ dice build kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS
    $ dice status kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS

Find the image in a tarball displayed by the :command:`status` command.

In order to run your image build, call :command:`qemu` as follows:

.. code:: bash

    $ qemu -drive \
        file=LimeJeOS-Leap-42.1.x86_64-1.42.1.raw,format=raw,if=virtio

