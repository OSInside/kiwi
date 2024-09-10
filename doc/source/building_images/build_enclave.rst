.. _eif:

Build an AWS Nitro Enclave
==============================

.. sidebar:: Abstract

   This page explains how to build AWS Nitro Enclaves. It covers the following topics:

   * how to build an AWS Nitro Enclave
   * how to test the enclave via QEMU

AWS Nitro Enclaves enables customers to create isolated compute environments
to further protect and securely process highly sensitive data such as personally
identifiable information (PII), healthcare, financial, and intellectual property
data within their Amazon EC2 instances. Nitro Enclaves uses the same Nitro
Hypervisor technology that provides CPU and memory isolation for EC2 instances.
For further details please visit https://aws.amazon.com/ec2/nitro/nitro-enclaves

To add an enclave build to your appliance, create a `type` element with
`image` set to `enclave` in the :file:`config.xml` file as shown below:

.. code:: xml

   <image schemaversion="{schema_version}" name="kiwi-test-image-nitro-enclave">
     <!-- snip -->
     <profiles>
       <profile name="default" description="CPIO: default profile" import="true"/>
       <profile name="std" description="KERNEL: default kernel" import="true"/>
     </profiles>
     <preferences>
       <type image="enclave" enclave_format="aws-nitro" kernelcmdline="reboot=k panic=30 pci=off console=ttyS0 i8042.noaux i8042.nomux i8042.nopnp i8042.dumbkbd random.trust_cpu=on rdinit=/sbin/init"/>
       <!-- additional preferences -->
     </preferences>
     <packages type="image" profiles="std">
        <package name="kernel"/>
     </packages>
     <!-- more packages -->
     <!-- snip -->
   </image>

The following attributes of the `type` element are relevant:

- `enclave_format`: Specifies the enclave target

  As of today only the `aws-nitro` enclave target is supported


- `kernelcmdline`: Specifies the kernel commandline suitable for the enclave

  An enclave is a system that runs completely in RAM loaded from
  an enclave binary format which includes the kernel, initrd and
  the kernel commandline suitable for the target system.

With the appropriate settings specified in :file:`config.xml`, you can build an
image using {kiwi}:

.. code:: bash

   $ sudo kiwi-ng system build \
         --description kiwi/build-tests/{exc_description_enclave} \
         --set-repo {exc_repo_rawhide} \
         --target-dir /tmp/myimage

The resulting image is saved in :file:`/tmp/myimage`, and the image can
be tested with QEMU:

.. code:: bash

   $ sudo qemu-system-x86_64 \
         -M nitro-enclave,vsock=c \
         -m 4G \
         -nographic \
         -chardev socket,id=c,path=/tmp/vhost4.socket \
         -kernel {exc_image_base_name_enclave}.eif

The image is now complete and ready to use. Access to the system is
possible via ssh through a vsock connection into the guest. To establish
a vsock connection it's required to forward the connection through the
guest AF_VSOCK socket. This can be done via a ProxyCommand setup of the
host ssh as follows:

.. code:: bash

   $ vi ~/bin/vsock-ssh.sh

   #!/bin/bash
   CID=$(echo "$1" | cut -d . -f 1)
   socat - VSOCK-CONNECT:$CID:22

.. code:: bash

   $ vi ~/.ssh/config

   host *.vsock
     ProxyCommand ~/bin/vsock-ssh.sh %h

After the ssh proxy setup login to the enclave with a custom vsock port
as follows:

.. code:: bash

   $ ssh root@21.vsock
