.. This file contains the documentation of the runtime configuration, but
   it is not directly included into the toctree, because it needs to be
   included in two places with only one label.
   => In one location it is included with a label preceeding it and in the
      other (the man page) without the label.

The Runtime Configuration File
------------------------------

KIWI supports an additional configuration file for runtime specific
settings that do not belong into the image description but which are
persistent and would be unsuitable for command line parameters.

The runtime configuration file must adhere to the `YAML
<https://yaml.org/>`_ syntax. KIWI searches for the runtime configuration
file in the following locations:

1. :file:`~/.config/kiwi/config.yml`

2. :file:`/etc/kiwi.yml`


The parameters that can be changed via the runtime configuration file are
illustrated in the following example:

.. code:: yaml

   xz:
     # Additional command line flags for `xz`
     # see `man xz` for details
     - options: -9e

   obs:
     # Override the URL to the Open Build Service (i.e. how repository
     # paths starting with `obs://` will be resolved).
     # This setting is useful for building a KIWI appliance locally, which is
     # hosted on a custom OBS instance.
     # defaults to: http://download.opensuse.org/repositories
     - download_url: https://build.my-domain.example/repositories

     # Specifies whether the Open Build Service instance is public or
     # private
     # defaults to true
     - public: true | false

   bundle:
     # Configure whether the image bundle should contain a XZ compressed
     # image result or not.
     - compress: true | false

   container:
     # Specify the compression algorithm for compressing container
     # images. Invalid entries are skipped.
     # Defaults to `xz`.
     - compress: xz | none

   iso:
     # Configure which tool KIWI will use to build ISO images. Invalid
     # entries are ignored.
     # Defaults to `xorriso`
     - tool_category: cdrtools | xorriso

   oci:
     # Specify the OCI archive tool that will be used to create container
     # archives for OCI compliant images.
     # Defaults to `umoci`.
     - archive_tool: umoci | buildah

   build_constraints:
     # Configure the maximum image size. Either provide a number in bytes
     # or specify it with the suffix `m`/`M` for megabytes or `g`/`G` for
     # gigabytes.
     # If the resulting image exceeds the specified value, then KIWI will
     # abort with an error.
     # The default is no size constraint.
     - max_size: 700m

   runtime_checks:
     # Provide a list of runtime checks that should be disabled. Checks
     # that do not exist but are present in this list are silently
     # ignored.
     - disable: check_image_include_repos_publicly_resolvable | \
         check_target_directory_not_in_shared_cache | \
         check_volume_label_used_with_lvm | \
         check_volume_setup_defines_multiple_fullsize_volumes | \
         check_volume_setup_has_no_root_definition | \
         check_container_tool_chain_installed | \
         check_boot_description_exists | \
         check_consistent_kernel_in_boot_and_system_image | \
         check_dracut_module_for_oem_install_in_package_list | \
         check_dracut_module_for_disk_oem_in_package_list | \
         check_dracut_module_for_live_iso_in_package_list | \
         check_dracut_module_for_disk_overlay_in_package_list | \
         check_efi_mode_for_disk_overlay_correctly_setup | \
         check_xen_uniquely_setup_as_server_or_guest | \
         check_mediacheck_only_for_x86_arch | \
         check_minimal_required_preferences
