# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#


class KiwiError(Exception):
    """
    **Base class to handle all known exceptions**

    Specific exceptions are implemented as sub classes of KiwiError

    Attributes

    :param string message: Exception message text
    """
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return format(self.message)


class KiwiArchiveSetupError(KiwiError):
    """
    Exception raised if an unsupported image archive type is used.
    """


class KiwiArchiveTarError(KiwiError):
    """
    Exception raised if impossible to determine which tar command
    version is installed on the underlying system
    """


class KiwiBootImageDumpError(KiwiError):
    """
    Exception raised if an instance of BootImage* can not be
    serialized on as file via pickle dump
    """


class KiwiBootImageSetupError(KiwiError):
    """
    Exception raised if an unsupported initrd system type is used.
    """


class KiwiBootLoaderConfigSetupError(KiwiError):
    """
    Exception raised if a configuration for an unsupported
    bootloader is requested.
    """


class KiwiBootLoaderGrubDataError(KiwiError):
    """
    Exception raised if no grub installation was found.
    """


class KiwiBootLoaderGrubFontError(KiwiError):
    """
    Exception raised if no grub unicode font was found.
    """


class KiwiBootLoaderGrubInstallError(KiwiError):
    """
    Exception raised if grub install to master boot record has failed.
    """


class KiwiBootLoaderGrubModulesError(KiwiError):
    """
    Exception raised if the synchronisation of modules from the
    grub installation to the boot space has failed.
    """


class KiwiBootLoaderGrubPlatformError(KiwiError):
    """
    Exception raised if an attempt was made to use grub on an
    unsupported platform.
    """


class KiwiBootLoaderGrubSecureBootError(KiwiError):
    """
    Exception raised if the Microsoft signed shim loader or
    grub2 loader could not be found in the image root system
    """


class KiwiBootLoaderInstallSetupError(KiwiError):
    """
    Exception raised if an installation for an unsupported
    bootloader is requested.
    """


class KiwiBootLoaderIsoLinuxPlatformError(KiwiError):
    """
    Exception raised if an attempt was made to use isolinux on
    an unsupported platform.
    """


class KiwiBootLoaderTargetError(KiwiError):
    """
    Exception raised if the target to read the bootloader path
    from is not a disk or an iso image.
    """


class KiwiBootLoaderZiplInstallError(KiwiError):
    """
    Exception raised if the installation of zipl has failed.
    """


class KiwiBootLoaderZiplPlatformError(KiwiError):
    """
    Exception raised if a configuration for an unsupported
    zipl architecture is requested.
    """


class KiwiBootLoaderZiplSetupError(KiwiError):
    """
    Exception raised if the data set to configure the zipl
    bootloader is incomplete.
    """


class KiwiBootStrapPhaseFailed(KiwiError):
    """
    Exception raised if the bootstrap phase of the system prepare
    command has failed.
    """


class KiwiBundleError(KiwiError):
    """
    Exception raised if the system bundle command has failed.
    """


class KiwiCommandError(KiwiError):
    """
    Exception raised if an external command called via a Command
    instance has returned with an exit code != 0 or could not
    be called at all.
    """


class KiwiCommandNotFound(KiwiCommandError):
    """
    Exception raised if any executable command cannot be found in
    the evironment PATH variable.
    """


class KiwiCommandNotLoaded(KiwiError):
    """
    Exception raised if a kiwi command task module could not be
    loaded.
    """


class KiwiCompressionFormatUnknown(KiwiError):
    """
    Exception raised if the compression format of the data could
    not be detected.
    """


class KiwiCompatError(KiwiError):
    """
    Exception raised if the given kiwi compatibility command line
    could not be understood by the compat option parser.
    """


class KiwiConfigFileNotFound(KiwiError):
    """
    Exception raised if no kiwi XML description was found.
    """


class KiwiContainerSetupError(KiwiError):
    """
    Exception raised if an error in the creation of the
    container archive happened.
    """


class KiwiContainerImageSetupError(KiwiError):
    """
    Exception raised if an attempt to create a container instance
    for an unsupported container type is performed.
    """


class KiwiDataStructureError(KiwiError):
    """
    Exception raised if the XML description failed to parse the
    data structure.
    """


class KiwiDebootstrapError(KiwiError):
    """
    Exception raised if not enough user data to call debootstrap
    were provided or the debootstrap has failed.
    """


class KiwiDescriptionConflict(KiwiError):
    """
    Exception raised if both, a description file and xml_content
    is provided
    """


class KiwiDescriptionInvalid(KiwiError):
    """
    Exception raised if the XML description failed to validate
    the XML schema.
    """


class KiwiDeviceProviderError(KiwiError):
    """
    Exception raised if a storage provide is asked for its
    managed device but no such device exists.
    """


class KiwiDiskBootImageError(KiwiError):
    """
    Exception raised if a kiwi boot image does not provide the
    requested data, e.g kernel, or hypervisor files.
    """


class KiwiDiskFormatSetupError(KiwiError):
    """
    Exception raised if an attempt was made to create a disk format
    instance of an unsupported disk format.
    """


class KiwiDiskGeometryError(KiwiError):
    """
    Exception raised if the disk geometry (partition table) could
    not be read or evaluated against their expected geometry and
    capabilities.
    """


class KiwiDistributionNameError(KiwiError):
    """
    Exception raised if the distribution name could not be found.
    The information is extracted from the boot attribute of the
    XML description. If no boot attribute is present or does not
    match the naming conventions the exception is raised.
    """


class KiwiExtensionError(KiwiError):
    """
    Exception raised if an extension section of the same namespace
    is used multiple times as toplevel section within the extension
    section. Each extension must have a single toplevel entry point
    qualified by its namespace
    """


class KiwiFileNotFound(KiwiError):
    """
    Exception raised if the requested file could not be found.
    """


class KiwiFileSystemSetupError(KiwiError):
    """
    Exception raised if an attempt was made to build an
    unsupported or unspecified filesystem.
    """


class KiwiFileSystemSyncError(KiwiError):
    """
    Exception raised if the data sync from the system into the
    loop mounted filesystem image failed.
    """


class KiwiFormatSetupError(KiwiError):
    """
    Exception raised if the requested disk format could not be created.
    """


class KiwiHelpNoCommandGiven(KiwiError):
    """
    Exception raised if the request for the help page is
    executed without a command to show the help for.
    """


class KiwiImageResizeError(KiwiError):
    """
    Exception raised if the request to resize a disk image failed.
    Reasons could be a missing raw disk reference or a wrong size
    specification.
    """


class KiwiImportDescriptionError(KiwiError):
    """
    Exception raised if the XML description data and scripts could
    not be imported into the root of the image.
    """


class KiwiInstallBootImageError(KiwiError):
    """
    Exception raised if the required files to boot an installation
    image could not be found, e.g kernel or hypervisor.
    """


class KiwiInstallMediaError(KiwiError):
    """
    Exception raised if a request for an installation media is made
    but the system image type is not an oem type.
    """


class KiwiInstallPhaseFailed(KiwiError):
    """
    Exception raised if the install phase of a system prepare command
    has failed.
    """


class KiwiPackagesDeletePhaseFailed(KiwiError):
    """
    Exception raised if the packages deletion phase in system prepare
    fails.
    """


class KiwiIsoLoaderError(KiwiError):
    """
    Exception raised if no isolinux loader file could be found.
    """


class KiwiIsoMetaDataError(KiwiError):
    """
    Exception raised if an inconsistency in the ISO header
    was found such like invalid eltorito specification or a
    broken path table.
    """


class KiwiIsoToolError(KiwiError):
    """
    Exception raised if an iso helper tool such as isoinfo
    could not be found on the build system.
    """


class KiwiKernelLookupError(KiwiError):
    """
    Exception raised if the search for the kernel image file failed
    """


class KiwiLiveBootImageError(KiwiError):
    """
    Exception raised if an attempt was made to use an
    unsupported live iso type.
    """


class KiwiLuksSetupError(KiwiError):
    """
    Exception raised if not enough user data is provided to
    setup the luks encryption on the given device.
    """


class KiwiLoadCommandUndefined(KiwiError):
    """
    Exception raised if no command is specified for a given
    service on the commandline.
    """


class KiwiLogFileSetupFailed(KiwiError):
    """
    Exception raised if the log file could not be created.
    """


class KiwiLoopSetupError(KiwiError):
    """
    Exception raised if not enough user data to create a
    loop device is specified.
    """


class KiwiMappedDeviceError(KiwiError):
    """
    Exception raised if the device to become mapped does not exist.
    """


class KiwiMountKernelFileSystemsError(KiwiError):
    """
    Exception raised if a kernel filesystem such as proc or sys
    could not be mounted.
    """


class KiwiMountSharedDirectoryError(KiwiError):
    """
    Exception raised if the host <-> image shared directory
    could not be mounted.
    """


class KiwiNotImplementedError(KiwiError):
    """
    Exception raised if a functionality is not yet implemented.
    """


class KiwiPackageManagerSetupError(KiwiError):
    """
    Exception raised if an attempt was made to create a package
    manager instance for an unsupported package manager.
    """


class KiwiPartitionerGptFlagError(KiwiError):
    """
    Exception raised if an attempt was made to set an unknown
    partition flag for an entry in the GPT table.
    """


class KiwiPartitionerMsDosFlagError(KiwiError):
    """
    Exception raised if an attempt was made to set an unknown
    partition flag for an entry in the MSDOS table.
    """


class KiwiPartitionerSetupError(KiwiError):
    """
    Exception raised if an attempt was made to create an instance
    of a partitioner for an unsupporte partitioner.
    """


class KiwiPrivilegesError(KiwiError):
    """
    Exception raised if root privileges are required but not granted.
    """


class KiwiProfileNotFound(KiwiError):
    """
    Exception raised if a specified profile does not exist in the
    XML configuration.
    """


class KiwiPxeBootImageError(KiwiError):
    """
    Exception raised if a required boot file e.g the kernel could
    not be found in the process of building a pxe image.
    """


class KiwiRaidSetupError(KiwiError):
    """
    Exception raised if invalid or not enough user data is provided
    to create a raid array on the specified storage device.
    """


class KiwiRepositorySetupError(KiwiError):
    """
    Exception raised if an attempt was made to create an instance of
    a repository for an unsupported package manager.
    """


class KiwiRepoTypeUnknown(KiwiError):
    """
    Exception raised if an unsupported repository type is specified
    for the corresponding package manager.
    """


class KiwiRequestedTypeError(KiwiError):
    """
    Exception raised if an attempt was made to build an image for
    an unsupported image type.
    """


class KiwiRequestError(KiwiError):
    """
    Exception raised if a package request could not be processed by
    the corresponding package manager instance.
    """


class KiwiResizeRawDiskError(KiwiError):
    """
    Exception raised if an attempt was made to resize the image disk
    to a smaller size than the current one. Simply shrinking a disk image
    file is not possible without data corruption because the partitions
    were setup to use the entire disk geometry as it fits into the file.
    A successful shrinking operation would require the filesystems and
    the partition table to be reduced which is not done by the provided
    simple storage resize method. In addition without the user overwriting
    the disk size in the XML setup, kiwi will calculate the minimum
    required size in order to store the data. Thus in almost all cases
    it will not be possible to store the data in a smaller disk.
    """


class KiwiResultError(KiwiError):
    """
    Exception raised if the image build result pickle information
    could not be created or loaded.
    """


class KiwiRootDirExists(KiwiError):
    """
    Exception raised if the specified image root directory already
    exists and should not be re-used.
    """


class KiwiRootInitCreationError(KiwiError):
    """
    Exception raised if the initialization of a new image root
    directory has failed.
    """


class KiwiRpmDatabaseReloadError(KiwiError):
    """
    Exception raised on error of an rpm DB dump -> reload process.
    """


class KiwiRpmDirNotRemoteError(KiwiError):
    """
    Exception raised if the provided rpm-dir repository is not local
    """


class KiwiRuntimeConfigFormatError(KiwiError):
    """
    Exception raised if the expected format in the yaml KIWI
    runtime config file does not match
    """


class KiwiRuntimeError(KiwiError):
    """
    Exception raised if a runtime check has failed.
    """


class KiwiSatSolverJobError(KiwiError):
    """
    Exception raised if a sat solver job can not be done, e.g because
    the requested package or collection does not exist in the registered
    repository metadata
    """


class KiwiSatSolverJobProblems(KiwiError):
    """
    Exception raised if the sat solver operations returned with solver
    problems e.g package conflicts
    """


class KiwiSatSolverPluginError(KiwiError):
    """
    Exception raised if the python solv module failed to load.
    The solv module is provided by SUSE's rpm package python-solv
    and provides a python binding to the libsolv C library
    """


class KiwiSchemaImportError(KiwiError):
    """
    Exception raised if the schema file could not be read
    by lxml.RelaxNG.
    """


class KiwiScriptFailed(KiwiError):
    """
    Exception raised if a user script returned with an exit code != 0.
    """


class KiwiSetupIntermediateConfigError(KiwiError):
    """
    Exception raised if the setup of the temporary image system
    configuration for the duration of the build process has
    failed.
    """


class KiwiSolverRepositorySetupError(KiwiError):
    """
    Exception raised if the repository type is not supported for
    the creation of a SAT solvable
    """


class KiwiSystemDeletePackagesFailed(KiwiError):
    """
    Exception raised if the deletion of a package has failed in
    the corresponding package manager instance.
    """


class KiwiSystemInstallPackagesFailed(KiwiError):
    """
    Exception raised if the installation of a package has failed in
    the corresponding package manager instance.
    """


class KiwiSystemUpdateFailed(KiwiError):
    """
    Exception raised if the package upgrade has failed in
    the corresponding package manager instance.
    """


class KiwiTargetDirectoryNotFound(KiwiError):
    """
    Exception raised if the specified target directory to store
    the image results was not found.
    """


class KiwiTemplateError(KiwiError):
    """
    Exception raised if the substitution of variables in a
    configuration file template has failed.
    """


class KiwiTypeNotFound(KiwiError):
    """
    Exception raised if no build type was found in the XML description.
    """


class KiwiUnknownServiceName(KiwiError):
    """
    Exception raised if an unknown service name was provided
    on the commandline.
    """


class KiwiUriOpenError(KiwiError):
    """
    Exception raised if the urllib urlopen request has failed
    """


class KiwiUriStyleUnknown(KiwiError):
    """
    Exception raised if an unsupported URI style was used in the
    source definition of a repository.
    """


class KiwiUriTypeUnknown(KiwiError):
    """
    Exception raised if the protocol type of an URI is unknown
    in the source definition of a repository.
    """


class KiwiValidationError(KiwiError):
    """
    Exception raised if the XML validation against the schema has failed.
    """


class KiwiVhdTagError(KiwiError):
    """
    Exception raised if the GUID tag is not provided in the
    expected format.
    """


class KiwiVolumeGroupConflict(KiwiError):
    """
    Exception raised if the requested LVM volume group already is
    in use on the build system.
    """


class KiwiVolumeManagerSetupError(KiwiError):
    """
    Exception raised if the preconditions for volume mangement
    support are not met or an attempt was made to create an
    instance of a volume manager for an unsupported volume
    management system.
    """


class KiwiVolumeRootIDError(KiwiError):
    """
    Exception raised if the root volume can not be found. This
    concept currently exists only for the btrfs subvolume system.
    """


class KiwiRootImportError(KiwiError):
    """
    Exception is raised when something fails during the root import
    procedure.
    """


class KiwiContainerBuilderError(KiwiError):
    """
    Exception is raised when something fails during a container image
    build procedure.
    """


class KiwiSizeError(KiwiError):
    """
    Exception is raised when the convertion from a given size in string
    format to a number.
    """


class KiwiCommandCapabilitiesError(KiwiError):
    """
    Exception is raised when some the CommandCapabilities methods fails,
    usually meaning there is some issue trying to parse some command output.
    """


class KiwiDecodingError(KiwiError):
    """
    Exception is raised on decoding literals failure
    """
