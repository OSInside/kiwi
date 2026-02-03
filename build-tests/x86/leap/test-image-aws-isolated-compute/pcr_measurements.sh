#!/bin/bash
#
# UKI PCR Measurement Script
# --------------------------
#
# Description:
#   This script is called by KIWI-NG during the image creation process
#   to calculate PCR measurements. It locates the UKI (kiwi.efi) in the
#   EFI/Linux directory, moves it to the EFI/BOOT directory, renames it
#   to the standard boot filename (e.g., BOOTX64.EFI), and uses
#   nitro-tpm-pcr-compute to calculate PCR4 and PCR7 values.
#
# Parameters (automatically passed by KIWI):
#   $1: Path to the raw disk image
#   $2: Root partition device (e.g., /dev/loop0p2)
#
# Output:
#   - Saves PCR measurements to <TARGET-DIR>/pcr_measurements.json in the build directory
#   - Kiwi execution stops in the case of failure
#
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Copyright 2024 SUSE LLC. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#
set -e -o pipefail

disk_image="$1"
root_device="$2"

build_dir=/usr/src/packages/OTHER
pcr_values_file="$build_dir/pcr_measurements.json"

if [ ! -b "$root_device" ]; then
    echo "ERROR: Root device not found at: $root_device"
    exit 1
fi

root_mount=$(findmnt -n -o TARGET "$root_device")
echo "INFO: Root partition ($root_device) mounted at: $root_mount"

efi_mount="${root_mount}/boot/efi"
echo "INFO: Checking EFI partition at: $efi_mount"

if ! mountpoint -q "$efi_mount"; then
    echo "ERROR: EFI partition not mounted at: $efi_mount"
    exit 1
fi

EFI_BINARY=$(
    find "$efi_mount/EFI/BOOT/" -name "BOOT*.EFI" \
        -printf "%f\n" 2>/dev/null |\
    head -n1
)

if [ -z "$EFI_BINARY" ]; then
    echo "ERROR: Could not find BOOT*.EFI in $efi_mount/EFI/BOOT/"
    exit 1
fi

if [ -f "$efi_mount/EFI/Linux/kiwi.efi" ]; then
    echo "INFO: Found kiwi.efi at: $efi_mount/EFI/Linux/kiwi.efi"

    echo "INFO: Removing existing $EFI_BINARY"
    rm -f "$efi_mount/EFI/BOOT/$EFI_BINARY"

    echo "INFO: Moving kiwi.efi to $EFI_BINARY location"
    cp "$efi_mount/EFI/Linux/kiwi.efi" "$efi_mount/EFI/BOOT/$EFI_BINARY"

    echo "INFO: Removing /EFI/Linux directory"
    rm -rf "$efi_mount/EFI/Linux"

    if [ -d "$efi_mount/EFI/systemd" ]; then
        echo "INFO: Removing /EFI/systemd directory"
        rm -rf "$efi_mount/EFI/systemd"
    fi

    if "$root_mount/usr/bin/nitro-tpm-pcr-compute" \
        --image "$efi_mount/EFI/BOOT/$EFI_BINARY" | tee "$pcr_values_file"
    then
        echo "SUCCESS: PCR measurements computed and saved to: $pcr_values_file"
    else
        echo "ERROR: Failed to compute PCR measurements for UKI"
        exit 1
    fi
else
    echo "ERROR: UKI not found !"
    echo "Expected UKI at location: $efi_mount/EFI/Linux/kiwi.efi"
    echo "DEBUG: Current EFI directory contents:"
    ls -R "$efi_mount/EFI/"
    exit 1
fi
