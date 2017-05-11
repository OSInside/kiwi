.. _container-building:

Building in a Self-Contained Environment
========================================

.. hint:: **Abstract**

   Users building images with KIWI face problems if they want
   to build an image matching one of the following criteria:

   * build should happen as non root user.

   * build should happen on a host system distribution for which
     no KIWI packages exists.

   * build happens on an incompatible host system distribution
     compared to the target image distribution. For example
     the host system rpm database is incompatible with the image
     rpm database and a dump/reload cycle is not possible
     between the two versions. Ideally the host system distribution
     is the same as the target image distribution.

   This document describes how to perform the build process in
   a Docker container using the Dice containment build system
   written for KIWI in order to address the issues listed above.

   The changes on the machine to become a build host will
   be reduced to the requirements of Dice and Docker.

Requirements
------------

The following components needs to be installed on the build system:

* Dice - a containment build system for KIWI.

* Docker - a container framework based on the Linux
  container support in the kernel.

* Docker Image - a docker build container for KIWI.

* optionally Vagrant - a framework to run, provision and control
  virtual machines and container instances. Vagrant has a very nice
  interface to provision a machine prior to running the actual build.
  It also supports docker as a provider which makes it a perfect fit
  for complex provisioning tasks in combination with the Docker
  container system.

* optionally libvirt - Toolkit to interact with the virtualization
  capabilities of Linux. In combination with vagrant, libvirt can
  be used as provider for provision and control full virtual
  instances running via qemu. As docker shares the host system
  kernel and thus any device, because KIWI needs to use privileged
  docker containers for building images, the more secure but less
  performant solution is to use virtual machines to run the KIWI
  build.

Installing and Setting up Dice
------------------------------

The Dice packages and sources are available at the following locations:

* Build service project:
  http://download.opensuse.org/repositories/Virtualization:/Appliances:/ContainerBuilder
* Sources: https://github.com/SUSE/dice

.. code:: bash

    $ sudo zypper in ruby2.1-rubygem-dice

Installing and Setting up Docker
--------------------------------

Docker packages are usually available with the used distribution.

.. code:: bash

    $ sudo zypper in docker

Make sure that the user, who is intended to build images, is a member
of the `docker` group. Run the following command:

.. code:: bash

    $ sudo useradd -G docker <builduser>

It is required to logout and login again to let this change
become active.

Once this is done you need to setup the Docker storage backend.
By default Docker uses the device mapper to manage the storage for
the containers it starts. Unfortunately, this does not work if the
container is supposed to build images because it runs into conflicts
with tools like :command:`kpartx` which itself maps devices using
the device mapper.

Fortunately, there is a solution for Docker which allows us to use
Btrfs as the storage backend. The following is only required if your
host system root filesystem is not btrfs:

.. code:: bash

    $ sudo qemu-img create /var/lib/docker-storage.btrfs 20g
    $ sudo mkfs.btrfs /var/lib/docker-storage.btrfs
    $ sudo mkdir -p /var/lib/docker
    $ sudo mount /var/lib/docker-storage.btrfs /var/lib/docker

    $ sudo vi /etc/fstab

      /var/lib/docker-storage.btrfs /var/lib/docker btrfs defaults 0 0

    $ sudo vi /etc/sysconfig/docker

      DOCKER_OPTS="-s btrfs"

Finally start the docker service:

.. code:: bash

    $ sudo systemctl restart docker

Installing and Setting up the Build Container
----------------------------------------------

In order to build in a contained environment Docker has to start a
privileged system container. Such a container must be imported before
Docker can use it. The build container is provided to you as a
service and build with KIWI in the project
at http://download.opensuse.org/repositories/Virtualization:/Appliances:/Images.
The result image is pushed to https://hub.docker.com/r/opensuse/dice.

When building with Dice, the container will be automatically fetched
from the docker registry. However this step can also be done prior to
calling :command:`dice` as follows:

.. code:: bash

    $ docker pull opensuse/dice:latest

.. note:: Optional step

    If a custom or newer version of the Build Container should be used,
    it is required to update the registry. This is because Dice always
    fetches the latest version of the Build Container from the registry.

    1. Download the .tar.bz2 file which starts with :file:`Docker-Tumbleweed`

    .. code:: bash

        $ wget http://download.opensuse.org/repositories/Virtualization:/Appliances:/Images/images/Docker-Tumbleweed.XXXXXXX.docker.tar.xz

    2. Import the downloaded tarball with the command :command:`docker`:

    .. code:: bash

        $ docker load -i Docker-Tumbleweed.XXXXXXX.docker.tar.xz

    3. Tag the container and push back to the registry

    .. code:: bash

        $ docker push opensuse/dice:latest


Installing and Setting up Vagrant
---------------------------------

.. note:: Optional step

    By default Dice shares the KIWI image description directory with
    the Docker instance. If more data from the host should be shared
    with the Docker instance we recommend to use Vagrant for this
    provision tasks.

Installing Vagrant is well documented at
https://www.vagrantup.com/docs/installation/index.html

Access to a machine started by Vagrant is done through SSH exclusively.
Because of that an initial key setup is required in the Docker image vagrant
should start. The KIWI Docker image includes the public key of the Vagrant
key pair and thus allows access. It is important to understand that the
private Vagrant key is not a secure key because the private key is not
protected.

However, this is not a problem because Vagrant creates a new
key pair for each machine it starts. In order to allow Vagrant the initial
access and the creation of a new key pair, it's required to provide access
to the insecure Vagrant private key. The following commands should not be
executed as root, but as the intended user to build images.

.. code:: bash

    $ mkdir -p ~/.dice/key
    $ cp -a /usr/share/doc/packages/ruby*-rubygem-dice/key ~/.dice/key


Configuring Dice
----------------

If you build in a contained environment, there is no need to have KIWI
installed on the host system. KIWI is part of the container and is only
called there. However, a KIWI image description and some metadata
defining how to run the container are required as input data.

Selecting a KIWI Template
-------------------------

If you don't have a KIWI description select one from the templates
provided at the GitHub project hosting example appliance descriptions.

.. code:: bash

    $ git clone https://github.com/SUSE/kiwi-descriptions

The descriptions hosted here also provides a default :file:`Dicefile`
as part of each image description.

The Dicefile
------------

The Dicefile is the configuration file for the dice buildsystem backend.
All it needs to know for a plain docker based build process is the
selection of the buildhost to be a Docker container. The Dicefile's
found in the above mentioned appliance descriptions look all like the
following:

.. code:: ruby

    Dice.configure do |config|
      config.buildhost = :DOCKER
    end

Building with Dice
------------------

If you have choosen to just use the default Dice configuration as
provided with the example appliance descriptions, the following example
command will build the image:

.. code:: bash

    $ cd <git-clone-result-kiwi-descriptions>

    $ dice build suse/x86_64/suse-leap-42.1-JeOS
    $ dice status suse/x86_64/suse-leap-42.1-JeOS


Buildsystem Backends
--------------------

Dice currently supports three build system backends:

1. Host buildsystem - Dice builds on the host like if you would call
   KIWI on the host directly.

2. Vagrant Buildsystem - Dice uses Vagrant to run a virtual system which
   could also be a container and build the image on this machine.

3. Docker buildsystem - Dice uses Docker directly to run the build in
   a container

The use of the Docker buildsystem has been already explained in the
above chapters. The following sections explains the pros and cons of
the other two available Buildsystem Backends.

Building with the Host Buildsystem
----------------------------------

Using the Host Buildsystem basically tells Dice to ssh into the
specified machine with the specified user and run KIWI. This is
also the information which needs to be provided in a Dicefile.
Using the Host Buildsystem is recommended if there are dedicated
build machines available to take over KIWI build jobs.

The Dicefile
------------

.. code:: ruby

    Dice.configure do |config|
      config.buildhost = "full-qualified-dns-name-or-ip-address"
      config.ssh_user = "vagrant"
    end

After these changes a :command:`dice build` command will make use
of the Host Buildsystem and starts the KIWI build process there.

.. note:: Provisioning of the Host Buildsystem

    There is no infrastructure in place which manages the machine
    specified as config.buildhost. This means it is currently in the
    responsibility of the user to make sure the specified machine
    exists and is accessible via the configured user. For the future
    we plan to implement a Public Cloud Buildsystem which then will
    allow provisioning and management of a public cloud instance
    e.g on Amazon EC2 in order to run the build. However we are
    not there yet.

Building with the Vagrant Buildsystem
-------------------------------------

Using the Vagrant Buildsystem should be considered if one or both of the
following use cases applies:

1. The build task requires additional content or logic before the build
   can start. Vagrant serves as provisioning system to share data
   from the host with the guest containers.

2. The build task should run in a completely isolated virtual machine
   environment. Vagrant in combination with the libvirt provider serves
   as both; The tool to interact with the virtualization capabilities
   to run and manage virtual machine instances and as provisioning system
   to share data from the host with the virtual machines.

The Dicefile
------------

The Dicefile in the context of Vagrant needs to know the user name to
access the instance. The reason for this is, in Vagrant access to the
system is handled over SSH.

.. code:: ruby

    Dice.configure do |config|
      config.ssh_user = "vagrant"
    end

The Vagrant setup for the Docker Provider
------------------------------------------

The following is an example for the first use case and describes how
to configure Dice to use Docker in combination with Vagrant as
provisioning system.

The Vagrantfile
---------------

The existence of a Vagrantfile tells Dice to use Vagrant as Buildsystem.
Once you call :command:`dice` to build the image it will
call :command:`vagrant` to bring up the container. In order to allow this,
we have to tell Vagrant to use Docker for this task and provide parameters
on how to run the container. At the same place the Dicefile exists we create
the Vagrantfile with the following content:

.. code:: ruby

    VAGRANTFILE_API_VERSION = "2"

    Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
      config.vm.provider "docker" do |d|
        d.image = "opensuse/dice:latest"
        d.create_args = ["-privileged=true", "-i", "-t"]
        # start the sshd in foreground to keep the container in running state
        d.cmd = ["/usr/sbin/sshd", "-D"]
        d.has_ssh = true
      end
    end

After these changes a :command:`dice build` command will make use
of the Vagrant build system and offers a nice way to provision
the Docker container instances prior to the actual KIWI build process.
Vagrant will take over the task to run and manage the docker container
via the `docker` tool chain.

The Vagrant setup for the libvirt Provider
------------------------------------------

The following sections are an example for the second use case and describes
how to configure Dice to use libvirt in combination with Vagrant as
provisioning and virtualization system.

The Vagrant Build Box
---------------------

Apart from the Docker build container the Dice infrastructure also
provides a virtual machine image also known as vagrant box which
contains a system ready to build images with KIWI.

Download the Vagrant build box which starts with
:file:`Vagrant-Libvirt-Tumbleweed` from the Open BuildService and add
the box to vagrant as follows:

.. code:: bash

    $ wget http://download.opensuse.org/repositories/Virtualization:/Appliances:/Images/images/Vagrant-Libvirt-Tumbleweed.XXXXXXX.vagrant.libvirt.box

    $ vagrant box add --provider libvirt --name kiwi-build-box Vagrant-Libvirt-Tumbleweed.XXXXXXX.vagrant.libvirt.box

    $ export VAGRANT_DEFAULT_PROVIDER=libvirt

The command :command:`vagrant box list` must list the box with
name `kiwi-build-box` as referenced in the following Vagrantfile setup.

The Vagrantfile
---------------

.. code:: ruby

    VAGRANTFILE_API_VERSION = "2"

    Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
      config.vm.box = "kiwi-build-box"

      config.vm.provider "libvirt" do |lv|
        lv.memory = "1024"
      end
    end

After these changes a :command:`dice build` command will make use
of the Vagrant build system and offers a nice way to provision
fully isolated qemu instances via libvirt prior to the actual KIWI
build process. Vagrant will take over the task to run and manage the
virtual machines via the `libvirt` tool chain.
