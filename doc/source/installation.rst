.. _kiwi-installation:

Installation
============

.. note::

   This document describes how to install {kiwi}.

Apart from the preferred method to install {kiwi} via a distribution
package manager, it is also available on `pypi <https://pypi.org/project/kiwi/>`__
and can be installed using Python's package manager pip as follows:

.. code:: shell-session

    $ sudo pip install kiwi

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

       $ sudo zypper addrepo \
             http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST> \
             kiwi-appliance-builder

4. Install {kiwi}:

   .. code:: shell-session

       $ sudo zypper --gpg-auto-import-keys install python3-kiwi


.. note:: Other Distributions

   If your distribution is not using :command:`zypper`, please use your
   package manager's appropriate command instead. For :command:`dnf`,
   as an example, that is:

   .. code:: shell-session

      $ sudo dnf config-manager \
            --add-repo https://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST>/Virtualization:Appliances:Builder.repo

      $ sudo dnf install python3-kiwi


Installation from Distribution Repositories
-------------------------------------------

Some Linux distributions ship {kiwi} in their official repositories. These
include **openSUSE** and **Fedora** since version 28. Note, these packages tend to
not be as up to date as the packages from OBS, so some features described
here might not exist yet.

.. note::

   There are many packages that contain the name *kiwi* in their name, some
   of these are not even python packages. Please double check the packages'
   description whether it is actually the {kiwi} Appliance builder before
   installing it. Please also note, depending on how the responsible
   packager has integrated {kiwi} into the distribution, the install
   name can be different from the instructions provided in:
   :ref:`installation-from-obs`

To install {kiwi} for the desired distribution, run the following command:

Leap/Tumbleweed:
  .. code:: shell-session

     $ sudo zypper install python3-kiwi

Fedora/Rawhide:
  .. code:: shell-session

     $ sudo dnf install kiwi-cli

.. _example-descriptions:

Example Appliance Descriptions
------------------------------

There are two places for example appliance descriptions:

The {kiwi} build tests:
  The {kiwi} project itself hosts a collection of appliance descriptions
  which are used for integration testing of the {kiwi} builder itself.
  These descriptions are required to build prior any {kiwi} release
  and are also used as the base for this documentation. Please check
  them out when working with this reference guide:

  .. code:: shell-session

      $ git clone https://github.com/OSInside/kiwi

      $ tree -L 3 kiwi/build-tests

The {kiwi} community descriptions project:
  There is a GitHub project hosting example appliance descriptions to be used
  with the next generation {kiwi}. Contributions from the community makes up
  the contents of this repository and users who need an example for a specific
  use case and distribution can clone the project as follows:

  .. code:: shell-session

      $ git clone https://github.com/OSInside/kiwi-descriptions
