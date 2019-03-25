.. _kiwi-installation:

Installation
============

.. hint::

   This document describes how to install KIWI. Apart from the preferred
   method to install KIWI via rpm, it is also available on `pypi
   <https://pypi.org/project/kiwi/>`__ and can be installed via pip.

.. _installation-from-obs:

Installation from OBS
---------------------

The most up to date packages of KIWI can be found on the Open Build Service
in the `Virtualization:Appliances:Builder
<https://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__
project.

To install KIWI, follow these steps:

1. Open the URL https://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder
   in your browser.

2. Right-click on the link of your preferred operating system and
   copy the URL. In Firefox it is the menu :menuselection:`Copy link address`.

3. Insert the copied URL from the last step into your shell. The ``DIST``
   placeholder contains the respective distribution.
   Use :command:`zypper addrepo` to add it to the list of your repositories:

   .. code-block:: shell-session

       $ sudo zypper addrepo http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST> appliance-builder

   If your distribution is not using :command:`zypper`, please use your
   package manager's appropriate command instead. For :command:`dnf` that
   is:

   .. code-block:: shell-session

      $ sudo dnf config-manager --add-repo https://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST>/Virtualization:Appliances:Builder.repo

4. Add the repositories' signing-key to your package manager's
   database. For rpm run:

   .. code-block:: shell-session

      $ sudo rpm --import https://build.opensuse.org/projects/Virtualization:Appliances:Builder/public_key

   And verify that you got the correct key:

   .. code-block:: shell-session

      $ rpm -qi gpg-pubkey-74cbe823-* | gpg2
      gpg: WARNING: no command supplied.  Trying to guess what you mean ...
      pub   dsa1024 2009-05-04 [SC] [expires: 2020-10-09]
            F7E82012C74FD0B85F5334DC994B195474CBE823
      uid           Virtualization:Appliances OBS Project <Virtualization:Appliances@build.opensuse.org>

5. Install KIWI:

   .. note:: Multipython packages

      This version of KIWI is provided as packages for python 2 and
      python 3. The following assumes that you will install the python 3 package.

   .. code-block:: shell-session

       $ sudo zypper in python3-kiwi


Installation from your distribution's repositories
--------------------------------------------------

.. note::

   There are many packages that contain the name KIWI in their name, some
   of these are even python packages. Please double check the packages'
   description whether it is actually the KIWI Appliance builder before
   installing it.


Some Linux distributions ship KIWI in their official repositories. These
include openSUSE Tumbleweed, openSUSE Leap and Fedora since
version 28. Note that these packages tend to not be as up to date as the
packages from OBS, so some features described here might not exist yet.

To install KIWI on openSUSE, run the following command:

.. code-block:: shell-session

   $ sudo zypper install python3-kiwi

On Fedora, use the following command instead:

.. code-block:: shell-session

   $ sudo dnf install kiwi-cli


Installation from PyPI
----------------------

KIWI can be obtained from the Python Package Index (PyPi) via Python's
package manager pip:

.. code-block:: shell-session

   $ pip install kiwi


.. _example-descriptions:

Example Appliance Descriptions
------------------------------

There is a GitHub project hosting example appliance descriptions to be used
with the next generation KIWI. Users who need an example to start with
should clone the project as follows:

.. code-block:: shell-session

    $ git clone https://github.com/SUSE/kiwi-descriptions
