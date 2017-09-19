#!/bin/bash
type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh
type merge_swap_to_fstab >/dev/null 2>&1 || . /lib/kiwi-filesystem-lib.sh

merge_swap_to_fstab
