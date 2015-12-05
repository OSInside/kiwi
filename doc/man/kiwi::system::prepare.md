# NAME

kiwi - Building Operating System Images

# SYNOPSIS

__kiwi__ system prepare --description=*directory* --root=*directory*

    [--type=*buildtype*]
    [--allow-existing-root]
    [--set-repo=*source,type,alias,priority*]
    [--ass-repo=*source,type,alias,priority*]

# DESCRIPTION

## __prepare__

Prepare and install a new system for chroot access

# OPTIONS

## __--description=directory__

The description must be a directory containing a kiwi XML description and optional metadata files

## __--root=directory__

The path to the new root directory of the system

## __--type=buildtype__

Set the build type. If not set the default XML specified build type will be used

## __--allow-existing-root__

Allow to use an existing root directory. Use with caution this could cause an inconsistent root tree if the existing contents does not fit to the additional installation

## __--set-repo=source,type,alias,priority__

Overwrite the repo source for the first XML repository with the
given repo source, type, alias or priority.

## __--add-repo=source,type,alias,priority__

Add a new repository with specified source, type, alias and priority

# REPOSITORY DETAILS

## __Priorities__

In kiwi this is a range from 1..99 whereas 1 is the highest priority and 99 the lowest. If no priority is set the repository is used with the default priority setup according to the used package manager. The package manager also defines how priorities can be used. Thus the kiwi provided numbers might be handled differently with respect to the used package manager backend. For more details please refer to the corresponding package manager documentation.

## __Repository types are:

1. yast2
2. rpm-md
3. rpm-dir

