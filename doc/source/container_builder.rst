Building in a self-contained Environment
========================================

.. topic:: Abstract

   This document describes how to build with KIWI using
   dice as a container buildsystem in order to eliminate
   any build host system requirements except the ones
   dice pulls in

Requirements
------------

The following components are needed in order to build in a
self-contained environment:

* :command:`dice` - a containment build system for KIWI.

* :command:`docker` - a container framework based on the Linux
  container support in the kernel.

* docker build container for KIWI.

* optionally :command:`vagrant` - a framework to run provision
  and control virtual machines and container instances. vagrant
  has a very nice way to provision a machine prior to running the
  actual build. vagrant also supports docker as a provider which
  makes it a perfect fit for complex provisioning tasks in
  combination with the docker container system.

Installing and Setting up dice
------------------------------

dice packages are available at the respective buildservice project
at http://download.opensuse.org/repositories/Virtualization:/Appliances. 
Sources are available at https://github.com/schaefi/dice.

.. code:: bash

    $ sudo zypper in ruby2.1-rubygem-dice

Installing and Setting up docker
--------------------------------

docker packages are usually available with the used distribution

.. code:: bash

    $ sudo zypper in docker

Make sure that the user who is intended to build images is a member
of the `docker` group by running the following command:

.. code:: bash

    $ sudo useradd -G docker <builduser>

It is required to logout and login again to let this change
become active.

Once this is done you need to setup the Docker storage backend.
By default Docker uses the device mapper to manage the storage for
the containers it starts. Unfortunately, this does not work if the
container is supposed to build images because it runs into conflicts
with tools like kpartx which itself maps devices using the device
mapper.

Fortunately, there is a solution for Docker which allows us to use
btrfs as the storage backend. The following is only required if your
host system root filesystem is not btrfs.

.. code:: bash

    $ sudo qemu-img create /var/lib/docker-storage.btrfs 20g
    $ sudo mkfs.btrfs /var/lib/docker-storage.btrfs
    $ sudo mkdir -p /var/lib/docker
    $ sudo mount /var/lib/docker-storage.btrfs /var/lib/docker

    $ sudo vi /etc/fstab

      /var/lib/docker-storage.btrfs /var/lib/docker btrfs defaults 0 0

    $ sudo vi /etc/sysconfig/docker

      DOCKER_OPTS="-s btrfs"

Finally start the docker daemon:

.. code:: bash

    $ sudo systemctl restart docker

Installing and Setting up the build container
----------------------------------------------

In order to build in a contained environment docker has to start a
privileged system container. Such a container must be imported before
docker can use it. The build container is provided to you as a
service and build with KIWI in the project
at https://build.opensuse.org/project/show/Virtualization:Appliances:Images
On a regular basis the result image is pushed
to https://hub.docker.com/r/schaefi/kiwi-build-box

There are two ways to import the build container to your local docker system

1. Download from the openSUSE Buildservice and manually import
2. Use docker to pull the box from dockerhub

Pull from dockerhub
-------------------

.. code:: bash

    $ docker pull schaefi/kiwi-build-box:latest

Download from the open BuildService
-----------------------------------

Download the .tar.bz2 file which starts with :file:`Docker-Tumbleweed`

.. code:: bash

    $ wget http://download.opensuse.org/repositories/Virtualization:/Appliances:/Images/images/Docker-Tumbleweed.XXXXXXX.docker.tar.xz

Import the downloaded tarball to docker as follows:

.. code:: bash

    $ cat Docker-Tumbleweed.XXXXXXX.docker.tar.xz | docker import - schaefi/kiwi-build-box:latest


Installing and Setting up vagrant
---------------------------------

.. note:: Optional step

    This step can be skipped if there are no complex provision tasks
    of the building environment required.

Installing vagrant is well documented at
https://docs.vagrantup.com/v2/installation/index.html

Access to a machine started by vagrant is done through ssh exclusively.
Because of that an initial key setup is required in the box vagrant should
start. The kiwi provided build boxes includes the public key of the vagrant
key pair and thus allows access. It is important to understand that the
private vagrant key is not a secure key because the private key is not
protected. However this is not a problem because vagrant creates a new
key pair for each machine it starts. In order to allow vagrant the initial
access and the creation of a new key pair, it's required to provide access
to the insecure vagrant private key. The following commands should not be
executed as root, but rather as the user intending to build images.

.. code:: bash

    $ mkdir -p ~/.dice/key
    $ cp -a /usr/share/doc/packages/ruby2.1-rubygem-dice/key ~/.dice/key


Building with dice
------------------

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
selection of the buildhost to be a docker container. The Dicefile's
found in the above mentioned appliance descriptions look all like the
following:

.. code:: ruby

    Dice.configure do |config|
      config.buildhost = :DOCKER
    end

Building with dice
------------------

If you have choosen to just use the default dice configuration as
provided with the example appliance descriptions, the following example
command will build the image.

.. code:: bash

    $ cd <git-clone-result-kiwi-descriptions>

    $ dice build suse/x86_64/suse-leap-42.1-JeOS
    $ dice status suse/x86_64/suse-leap-42.1-JeOS/


Buildsystem backends
--------------------

dice currently supports three build system backends:

1. `host buildsystem` - dice builds on the host like if you would call
   kiwi on the host directly

2. `vagrant buildsystem` - dice uses vagrant to run a virtual system which
   could also be a container and build the image on this machine

3. `docker buildsystem` - dice uses docker directly to run the build in
   a container

So far we have described how to use dice with the plain docker
buildsystem. If the build task requires additional content or logic
before the build can start the vagrant buildsystem configured to use
docker provides a nice interface to this provisioning tasks.

Building with the vagrant buildsystem
-------------------------------------

The following sections describes how to setup dice to use docker in
combination with vagrant as provisioning system

The Dicefile
------------

The Dicefile in the context of vagrant needs to know the username to
access the container. This is because in vagrant access to the system
is handled over ssh. vagrant is also the default buildsystem in dice
which means in contrast to the docker buildsystem we do not have to
actively select it.

.. code:: ruby

    Dice.configure do |config|
      config.ssh_user = "vagrant"
    end

The Vagrantfile
---------------

Once you call dice to build the image it will call vagrant to bring up the
container. In order to allow vagrant to do this we have to tell vagrant that
it should use Docker for this task and provide parameters on how to run the
container. At the same place the Dicefile exists we create the Vagrantfile
with the following content:

.. code:: ruby

    VAGRANTFILE_API_VERSION = "2"

    Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
      config.vm.provider "docker" do |d|
        d.image = "schaefi/kiwi-build-box:latest"
        d.create_args = ["-privileged=true", "-i", "-t"]
        # start the sshd in foreground to keep the container in running state
        d.cmd = ["/usr/sbin/sshd", "-D"]
        d.has_ssh = true
      end
    end

After these changes a :command:`dice build` command will make use
of the vagrant build system and offers you a nice way to provision
the docker container instances prior to the actual KIWI build process.
