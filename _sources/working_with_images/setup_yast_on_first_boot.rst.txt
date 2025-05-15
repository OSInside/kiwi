.. _yast-on-boot:

Setting Up YaST at First Boot
=============================

.. sidebar:: Abstract

    This page provides information how to setup the {kiwi}
    XML description to start the SUSE YaST system setup
    utility at first boot of the image

To be able to use YaST in a non interactive way, create a
YaST profile which tells the autoyast module what to do.
To create the profile, run:

.. code:: bash

    yast autoyast

Once the YaST profile exists, update the {kiwi} XML description
as follows:

1. Edit the {kiwi} XML file and add the following package to
   the `<packages type="image">` section:

   .. code:: xml

       <package name="yast2-firstboot"/>

2. Copy the YaST profile file as overlay file to your {kiwi} image
   description overlay directory:

   .. code:: bash

       cd IMAGE_DESCRIPTION_DIRECTORY
       mkdir -p root/etc/YaST2
       cp PROFILE_FILE root/etc/YaST2/firstboot.xml

3. Copy and activate the YaST firstboot template.
   This is done by the following instructions which needs to be written
   into the {kiwi} :file:`config.sh` which is stored in the image
   description directory:

   .. code:: bash

       sysconfig_firsboot=/etc/sysconfig/firstboot
       sysconfig_template=/var/adm/fillup-templates/sysconfig.firstboot
       if [ ! -e "${sysconfig_firsboot}" ]; then
           cp "${sysconfig_template}" "${sysconfig_firsboot}"
       fi

       touch /var/lib/YaST2/reconfig_system
