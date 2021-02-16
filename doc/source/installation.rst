.. _kiwi-installation:

Installation
============

.. note::

   This document describes how to install {kiwi}. Apart from the preferred
   method to install {kiwi} via rpm, it is also available on `pypi
   <https://pypi.org/project/kiwi/>`__ and can be installed via pip.

.. _installation-from-obs:

Installation from OBS
---------------------

The most up to date packages of {kiwi} can be found on the Open Build Service
in the `Virtualization:Appliances:Builder
<https://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__
project.

To install {kiwi}, follow these steps:

1. Open the URL https://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder
   in your browser.

2. Right-click on the link of your preferred operating system and
   copy the URL. In Firefox it is the menu :menuselection:`Copy link address`.

3. Insert the copied URL from the last step into your shell. The ``DIST``
   placeholder contains the respective distribution.
   Use :command:`zypper addrepo` to add it to the list of your repositories:

   .. code:: shell-session

       $ sudo zypper addrepo http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST> appliance-builder

   If your distribution is not using :command:`zypper`, please use your
   package manager's appropriate command instead. For :command:`dnf` that
   is:

   .. code:: shell-session

      $ sudo dnf config-manager --add-repo https://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST>/Virtualization:Appliances:Builder.repo

4. Add the repositories' signing-key to your package manager's
   database. For rpm run:

   .. code:: shell-session

      $ sudo rpm --import https://build.opensuse.org/projects/Virtualization:Appliances:Builder/public_key

   And verify that you got the correct key:

   .. code:: shell-session

      $ rpm -qi gpg-pubkey-74cbe823-* | gpg2
      gpg: WARNING: no command supplied.  Trying to guess what you mean ...
      pub   dsa1024 2009-05-04 [SC] [expires: 2020-10-09]
            F7E82012C74FD0B85F5334DC994B195474CBE823
      uid           Virtualization:Appliances OBS Project <Virtualization:Appliances@build.opensuse.org>

.. note::

   :command:`rpm` requires network utilities in order to download and
   import remote keys. Make sure :command:`curl` is installed before
   trying to import remote keys using :command:`rpm`. 
   
   Alternatively, the package manager, if not executed in non-interactive mode,
   will ask you to trust or not the public key of the new repository when
   refreshing repositories or installing new packages. If trusted the package
   manager will automatically import it.

5. Install {kiwi}:

   .. code:: shell-session

       $ sudo zypper in python3-kiwi


Installation from your distribution's repositories
--------------------------------------------------

.. note::

   There are many packages that contain the name {kiwi} in their name, some
   of these are even python packages. Please double check the packages'
   description whether it is actually the {kiwi} Appliance builder before
   installing it.


Some Linux distributions ship {kiwi} in their official repositories. These
include openSUSE Tumbleweed, openSUSE Leap, and Fedora since
version 28. Note, these packages tend to not be as up to date as the
packages from OBS, so some features described here might not exist yet.

To install {kiwi} on openSUSE, run the following command:

.. code:: shell-session

   $ sudo zypper install python3-kiwi

On Fedora, use the following command instead:

.. code:: shell-session

   $ sudo dnf install kiwi-cli


Installation from PyPI
----------------------

{kiwi} can be obtained from the Python Package Index (PyPi) via Python's
package manager pip:

.. code:: shell-session

   $ pip install kiwi


.. _example-descriptions:

Example Appliance Descriptions
------------------------------

There is a GitHub project hosting example appliance descriptions to be used
with the next generation {kiwi}. Users who need an example to start with
should clone the project as follows:

.. code:: shell-session

    $ git clone https://github.com/OSInside/kiwi-descriptions
