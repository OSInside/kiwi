Building in the Open Buildservice
=================================

.. hint:: **Abstract**

   This document gives a brief overview how to build images with
   KIWI in version |version| inside of the Open Buildservice.
   A tutorial on the Open Buildservice itself can be found here:
   https://en.opensuse.org/openSUSE:Build_Service_Tutorial


The next generation KIWI is fully integrated with the build service.
In order to start it's best to checkout one of the integration test
image build projects from the base Testing project
`Virtualization:Appliances:Images:Testing_ARCH` at:

https://build.opensuse.org

In order to use the next generation KIWI to build an appliance in the
build service it is required to add the Builder project as
repository to the KIWI XML configuration like in the following example:

.. code:: xml

 <repository type="rpm-md" alias="kiwi-next-generation">
     <source path="obs://Virtualization:Appliances:Builder/Factory"/>
 </repository>
