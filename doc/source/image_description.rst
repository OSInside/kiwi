.. _image-description:

Image Description
=================

.. note::

   This document explains the toplevel structure of the
   {kiwi} image description document for version |version|

.. toctree::
   :maxdepth: 1

   image_description/elements.rst


Main Root
---------

.. code:: xml

   <image/>

The mandatory :ref:`sec.image` element represents the root (top-level element) of
an image description. All other elements must be descendants of this
element. There can be only one `image` element.

Image Identity
--------------

.. code:: xml

   <description/>

The mandatory :ref:`sec.description` element contains information about the author,
contact, license and the specification about the use case of this
image. All data together forms the identity card of the image.
There can be only one `description` element

Image Preferences
-----------------

.. code:: xml

   <preferences/>

The mandatory :ref:`sec.preferences` element contains information to classify
the image and to describe the layout. All data about the image type, its
version, the partition layout and much more is specified here. There can be
multiple `preferences` elements

Image Software Sources
----------------------

.. code:: xml

   <repository/>

The mandatory :ref:`sec.repository` element contains information where to find the
software packages that are used to build the image. There can be
multiple `repository` elements

Image Content Setup
-------------------

.. code:: xml

   <packages/>

The mandatory :ref:`sec.packages` element contains information to list which
software should be installed from the configured repositories
into the image. Software can be defined as names for packages,
collections, archives or products. There can be multiple
`packages` elements

Image Users
-----------

.. code:: xml

   <users/>

The optional :ref:`sec.users` element contains information about system users
to be created inside of the image. There can be multiple `users`
elements

Image Namespace
---------------

.. code:: xml

   <profiles/>

The optional :ref:`sec.profiles` element contains information to create one
or more namespaces to an image description. The namespace can be
used with any of the above elements and therefore tie them into
a namespace which can be selected at call time of {kiwi}

Image Includes
--------------

.. code:: xml

   <include from="filename.xml"/>

The optional :ref:`sec.include` element allows to drop in the contents
of the specified :file:`filename.xml` file at the place were the `include`
statement was specified in the document. The `include` statement is
only allowed as descendant of the root (top-level element) of the
image description.
