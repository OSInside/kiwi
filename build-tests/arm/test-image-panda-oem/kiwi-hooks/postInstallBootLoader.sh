# On second boot, the rootfs is no longer tmpfs and dracut would interpret the
# command line argument, remove it again from the config
for file in /etc/sysconfig/bootloader /etc/default/grub /boot/boot.script; do
	[ -e "$file" ] && sed -i 's/rootflags=size=100%//' $file
done

#==========================================
# Recreate boot.script after first boot
#------------------------------------------
if [ -x /usr/bin/mkimage ]; then
	mkimage -A arm -O linux -a 0 -e 0 -T script -C none \
		-n 'Boot-Script' -d /boot/boot.script /boot/boot.scr
	if [ ! $? = 0 ]; then
		Echo "Failed to create boot script image"
	fi
fi

if [ "panda" = "mustang" -o "panda" = "m400" ]; then
	#==========================================
	# create uImage and uInitrd for x-gene
	#------------------------------------------
	/usr/bin/mkimage -A arm -O linux -C none -T kernel -a 0x00080000           \
	                 -e 0x00080000 -n Linux -d /boot/Image /boot/uImage
	/usr/bin/mkimage -A arm -O linux -T ramdisk -C none -a 0 -e 0 -n initramfs \
	                 -d /boot/initrd /boot/uInitrd
fi

if [ "panda" = "raspberrypi" -o "panda" = "raspberrypi2" -o "panda" = "raspberrypi3" ]; then
	#==========================================
	# convert GPT to hybrid GPT again
	#------------------------------------------
        echo "r
h
1 2 3
n
c
n
83
y
83
n
w
y" > /gdisk.tmp
	/usr/sbin/gdisk /dev/mmcblk0 < /gdisk.tmp
	rm -f /gdisk.tmp
fi

# Fix up grub2 efi installation on 32bit arm (shouldn't hurt elsewhere)
if grep -q boot/efi /etc/fstab; then
	mkdir -p /boot/efi
	mount /boot/efi
	/sbin/update-bootloader --reinit
fi
