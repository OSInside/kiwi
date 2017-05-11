.. _kiwi-installation:

Installation
============

.. hint::

   This document describes how to install KIWI. Apart from the preferred
   method to install KIWI via rpm, it is also provided on pypi and can
   be installed via pip.

KIWI can be installed with different methods. For this guide, only the
installation as a packages through a package manager is described.

Packages for the new KIWI version are provided at the `openSUSE
buildservice <http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder>`__.

To install KIWI, do:

1. Open the URL http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder
   in your browser.

2. Right-click on the link of your preferred operating system and
   copy the URL. In Firefox it is the menu :menuselection:`Copy link address`.

3. Insert the copied URL from the last step in your shell. The ``DIST``
   placeholder contains the respective distribution. Use :command:`zypper ar`
   to add it to your list of repositories:

   .. code-block:: shell-session

       $ sudo zypper ar -f http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST>

4. Install KIWI:

   .. note:: Multipython packages

      This version of KIWI is provided for python 2 and python 3 versions.
      The following information is based on the installation of the
      python3-kiwi package

   .. code-block:: shell-session

       $ sudo zypper in python3-kiwi

.. _example-descriptions:

Example Appliance Descriptions
------------------------------

For use with the next generation KIWI there is also a GitHub project
hosting example appliance descriptions. Users who need an example to
start with should checkout the project as follows:

.. code:: bash

    $ git clone https://github.com/SUSE/kiwi-descriptions
