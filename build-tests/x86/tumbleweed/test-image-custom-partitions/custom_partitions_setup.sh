image_file=$1

root_device=$2

loop_name=$(basename $root_device | cut -f 1-2 -d'p')

disk_device=/dev/${loop_name}

# mount root part
root=$(mktemp -d /tmp/rootmount-XXX)
mount /dev/${loop_name}p5 $root || exit 1

# move root part contents to individual partitions
part=$(mktemp -d /tmp/partmount-XXX)
log_uuid=$(blkid -s UUID -o value /dev/${loop_name}p6)
mount /dev/${loop_name}p6 $part && mv $root/var/log/* $part/
umount --lazy $part && rmdir $part

part=$(mktemp -d /tmp/partmount-XXX)
audit_uuid=$(blkid -s UUID -o value /dev/${loop_name}p7)
mount /dev/${loop_name}p7 $part && mv $root/var/audit/* $part/
umount --lazy $part && rmdir $part

part=$(mktemp -d /tmp/partmount-XXX)
var_uuid=$(blkid -s UUID -o value /dev/${loop_name}p4)
mount /dev/${loop_name}p4 $part && mv $root/var/* $part/
umount --lazy $part && rmdir $part

echo "UUID=$var_uuid /var ext4 defaults 0 0" >> $root/etc/fstab
echo "UUID=$log_uuid /var/log ext4 defaults 0 0" >> $root/etc/fstab
echo "UUID=$audit_uuid /var/audit ext4 defaults 0 0" >> $root/etc/fstab

# umount root part
umount --lazy $root && rmdir $root

# cleanup maps
partx --delete $disk_device

exit 0
