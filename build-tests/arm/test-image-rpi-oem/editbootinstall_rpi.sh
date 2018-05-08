#!/bin/bash

set -x

diskname=$1
devname="$2"
loopname="${devname%*p2}"
loopdev=/dev/${loopname#/dev/mapper/*}

#==========================================
# copy Raspberry Pi firmware to EFI partition
#------------------------------------------
echo "RPi EFI system, installing firmware on ESP"
mkdir -p ./mnt-pi
mount ${loopname}p1 ./mnt-pi
( cd boot/vc; tar c . ) | ( cd ./mnt-pi/; tar x )
umount ./mnt-pi
rmdir ./mnt-pi

#==========================================
# Change partition label type to MBR
#------------------------------------------
#
# The target system doesn't support GPT, so let's move it to
# MBR partition layout instead.
#
# Also make sure to set the ESP partition to type 0xc so that
# broken firmware (Rpi) detects it as FAT.
#
# Use tabs, "<<-" strips tabs, but no other whitespace!
cat > gdisk.tmp <<-'EOF'
		x
		r
		g
		t
		1
		c
		w
		y
	EOF
dd if=$loopdev of=mbrid.bin bs=1 skip=440 count=4
gdisk $loopdev < gdisk.tmp
dd of=$loopdev if=mbrid.bin bs=1 seek=440 count=4
rm -f mbrid.bin
rm -f gdisk.tmp
