.. _yast-on-boot:

Setting Up YAST at First Boot
=============================

.. sidebar:: Abstract

    This page provides information how to setup the KIWI
    XML description to start the SUSE YAST system setup
    utility at first boot of the image

To be able to use YAST in a non interactive way, you need to
create a YAST profile which tells it what to do. To create the
profile, run:

.. code:: bash

    yast autoyast

Once the YAST profile exists, update the KIWI XML description
as follows:

1. Edit the KIWI XML file and add the following package to
   the `<packages type="image">` section:

   .. code:: xml

       <package name="yast2-firstboot"/>

2. Copy the YAST profile file as overlay file to your KIWI image
   description overlay directory:

   .. code:: bash

       cd IMAGE_DESCRIPTION_DIRECTORY
       mkdir -p root/etc/YaST2
       cp PROFILE_FILE root/etc/YaST2/firstboot.xml

3. Copy and activate the YAST firstboot template.
   This is done by the following instructions which needs to be written
   into the KIWI :file:`config.sh` which also lives in the image
   description directory:

   .. code:: bash

       sysconfig_firsboot=/etc/sysconfig/firstboot
       sysconfig_template=/var/adm/fillup-templates/sysconfig.firstboot
       if [ ! -e "${sysconfig_firsboot}" ]; then
           cp "${sysconfig_template}" "${sysconfig_firsboot}"
       fi

       touch /var/lib/YaST2/reconfig_system
