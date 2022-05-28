#!/bin/dash

set -ex

# copy Raspberry Pi boot data to "EFI" part...
#==========================================
# copy firmware
#------------------------------------------
cp -a /usr/lib/linux-firmware-raspi/* /boot/efi

#==========================================
# copy device tree's
#------------------------------------------
cp -a /usr/lib/firmware/*-raspi/device-tree/overlays /boot/efi/
cp -a /usr/lib/firmware/*-raspi/device-tree/broadcom/* /boot/efi/

#==========================================
# copy initrd and kernel
#------------------------------------------
cp /boot/initrd.img-*-raspi /boot/efi/initrd.img
cp /boot/vmlinuz-*-raspi /boot/efi/vmlinuz

#==========================================
# copy u-boot
#------------------------------------------
cp /usr/lib/u-boot/rpi_3/u-boot.bin /boot/efi/uboot_rpi_3.bin
cp /usr/lib/u-boot/rpi_4/u-boot.bin /boot/efi/uboot_rpi_4.bin
cp /usr/lib/u-boot/rpi_arm64/u-boot.bin /boot/efi/uboot_rpi_arm64.bin

#==========================================
# create u-boot loader config
#------------------------------------------
echo "console=serial0,115200 dwc_otg.lpm_enable=0 console=tty1 root=LABEL=ROOT rd.kiwi.debug rootfstype=xfs rootwait fixrtc" > /boot/efi/cmdline.txt

mkimage -A arm64 -O linux -T script -C none -d /boot/efi/boot.cmd \
    /boot/efi/boot.scr
