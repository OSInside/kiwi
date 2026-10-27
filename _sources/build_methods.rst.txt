.. _build_methods:

Alternative Build Methods
=========================

.. note:: **Abstract**

   Besides building an image directly on the build host with the
   `kiwi-ng system build` command, {kiwi} provides alternative
   methods to build images. The following sections describe
   these methods and the use cases they address.

.. toctree::
   :maxdepth: 1

   build_methods/build_self_contained
   build_methods/build_based_on_containers

The `boxbuild` command runs the {kiwi} build inside of a self-contained
virtual machine or container, called a box. This keeps the build host
free from the build tool chain, allows building as a non-root user,
and allows building images for other distributions than the one
running on the build host. See :ref:`self_contained` for details.

The `stash` and `stackbuild` commands store {kiwi} built root trees as
OCI containers and build images on top of one or more of those
containers. This allows rebuilding an image without access to the
original software repositories, as well as turning existing containers
into any other image type supported by {kiwi}. See :ref:`stackbuild`
for details.
