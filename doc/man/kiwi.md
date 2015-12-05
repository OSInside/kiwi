# NAME

kiwi - Building Operating System Images

# SYNOPSIS

__kiwi__ [global-options] *servicename* *command* [*args*...]

# DESCRIPTION

KIWI is a command line tools for building images for Linux

# SERVICE NAMES

## __image__

Prepare and build new images

# COMMANDS

Each service provides a collection of commands which are loaded as plugin when the command is requested. The following chapter lists the available commands for each service. In addition every service command provides an extra manual page with detailed information about the command capabilities using the __help__ command

## __kiwi__ __image__ __prepare__ help

Installation and management of new image root directories

  * preparation and installation
  * upgrade root tree with latest repo updates
  * maintenance, e.g add software package

# GLOBAL OPTIONS

## __--debug__

Enable debugging mode. In this mode kiwi is more verbose and provides information useful to clarify processing issues.

## --profile=*name*

Comma separated list of profile names. The kiwi XML description can use
profiles to assign a section or a collection of sections into a namespace.
The profile option allows to select one or more of those namespaces
