#!/bin/bash

set -ex

image_fs=$1
  
root_partnum=$2

root_device=/dev/mapper/loop*p${root_partnum}

loop_name=$(basename $root_device | cut -f 1-2 -d'p')

disk_device=/dev/${loop_name}

#==========================================
# Change partition label type to MBR
#------------------------------------------
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
dd if=$disk_device of=mbrid.bin bs=1 skip=440 count=4
gdisk $disk_device < gdisk.tmp
dd of=$disk_device if=mbrid.bin bs=1 seek=440 count=4
rm -f mbrid.bin
rm -f gdisk.tmp
