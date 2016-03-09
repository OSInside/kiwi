# KIWI—Next Generation

[![Build Status](https://travis-ci.org/SUSE/kiwi.svg?branch=master)](https://travis-ci.org/SUSE/kiwi)
[![Health](https://landscape.io/github/SUSE/kiwi/master/landscape.svg?style=flat)](https://landscape.io/github/SUSE/kiwi/master)

This is a rewrite of the former KIWI appliance builder which
you can find here: https://github.com/openSUSE/kiwi.

## Contents

  * [Motivation](#motivation)
  * [Installation](#installation)
  * [Quick Start](#quick-start)
  * [Supported Distributions](#supported-distributions)
  * [Dropped Features](#dropped-features)
  * [Contributing](#contributing)
  * [Developing](#developing)
  * [Packaging and Versioning](#packaging-and-versioning)
  * [Documentation](#documentation)
  
## Motivation

During the last years KIWI has evolved a lot: Many features were
added, even some which are not in use anymore because new technologies
made them obsolete. There is a lot of legacy code in KIWI to support
older distributions. In order to become free from legacy code
the decision to provide a new version which can co-exist with the
former implementation was made.

However, the current design and the lack of tests in core parts of the
former code base, basically prevents a major refactoring as I see it
required. Because of that, a rewrite of KIWI with a stable version in
the background seems to be the best way.

Users will be able to use both versions in parallel. Also the new
KIWI will be fully compatible with the current format of the image
description. This means, you can build an image from the same image
description with the old and the new KIWI, if the new KIWI supports
the distribution and all features the image description has
configured.

## Installation

Packages for the new KIWI version are provided at the
[openSUSE buildservice](https://build.opensuse.org/package/show/Virtualization:Appliances:Builder/python3-kiwi)

Add the repository with `zypper ar` (see following code) and replace the
distribution placeholder. The best approach is to click on the desired
distribution from the buildservice link above and there follow the
__Go to download repository__ link

```bash
$ zypper ar -f \
    http://download.opensuse.org/repositories/Virtualization:/Appliances:/Builder/<DIST>
$ zypper in python3-kiwi
```

Please note the package uses the alternatives mechanism to setup
a symbolic link named `kiwi` to the real executable named `kiwi-py3`.
If the link target `/usr/bin/kiwi` already exists on your system, the
alternative setup will skip the creation of the link target because it
already exists.

## Quick Start

Along with the appliance builder there is also a GitHub project hosting
example image descriptions. The following shows how to build your first
image.

```bash
$ git clone https://github.com/SUSE/kiwi-descriptions

$ kiwi-py3 --type vmx system build \
       --description kiwi-descriptions/suse/x86_64/suse-leap-42.1-JeOS \
       --target-dir /tmp/myimage

$ cd /tmp/myimage

$ qemu -drive \
    file=LimeJeOS-Leap-42.1.x86_64-1.42.1.raw,format=raw,if=virtio
```

## Supported Distributions

This version of KIWI is targeted to build appliances for distributions
which are equal or newer compared to the following list:

* SUSE Linux Enterprise 12
* Red Hat Enterprise 7
* openSUSE 13.2
* openSUSE Leap 42
* openSUSE Tumbleweed

For anything older please consider to use the former
KIWI version __v7.x.x__

## Dropped Features

The following features have been dropped from KIWI:

* Split systems

  The legacy kiwi version supports building of split systems which
  uses a static definition of files and directories marked as read-only
  or read-write. Evolving technologies like overlayfs makes this
  feature obsolete.

* ZFS filesystem

  The successor for zfs is btrfs in the opensource world. All major
  distributions put on btrfs. This and the proprietary attitude of
  zfs obsoletes the feature.

* Reiserfs filesystem

  The number of people using this filesystem is decreasing. For
  image building reiserfs was an interesting filesystem however with
  btrfs and xfs there are good non inode based alternatives out there.
  Therefore we don't continue supporting reiserfs.

* Btrfs seed based live systems

  A btrfs seed device is an alternative for other copy on write
  filesystems like overlayfs. Unfortunately the stability of the seed
  device when used as cow part in a live system was not as good as
  we provide with overlayfs and clicfs. Therefore this variant is
  no longer supported. We might think of adding this feature back
  if people demand it.

* VDI image subformat

  The vdi disk image format is supported by the legacy kiwi version
  but we are not aware of any user. The missing business perspective
  makes this feature obsolete.

## Contributing

The core appliance builder is developed in Python and follows the
test driven development rules. The XML, schema, and stylesheets are
taken from the old version of KIWI. Also the entire boot code
(written in bash) is taken from the old KIWI codebase.

The Python project uses `pyvenv` to setup a development environment
for the desired Python version. The script `pyvenv` is already
installed when using Python 3.3 and higher (see https://docs.python.org/3.3/whatsnew/3.3.html#pep-405-virtual-environments for details).

The following procedure describes how to create such an environment:

1. Create the virtual environment:

   ```
$ pyvenv .env3
```

2. Activate the virtual environment:

   ```
$ source .env3/bin/activate
```

3. Install KIWI requirements inside the virtual environment:

   ```
$ pip3.4 install -r .virtualenv.dev-requirements.txt
```

4. Install KIWI in "development mode":

   ```
$ ./setup.py develop
```

You're done!

Once the development environment is activated and initialized with
the project required Python modules, you are ready to work.

The __develop__ target of the `setup.py` script automatically creates
the application entry point called `kiwi`, which allows to simply
call the application from the current code base:

   ```
$ kiwi-py3 --help
```

In order to leave the development mode just call:

```
$ deactivate
```

To resume your work, change into your local Git repository and
run `source .env3/bin/activate` again. Skip step 3 and 4 as
the requirements are already installed.


## Developing and Running Test Cases

When developing KIWI, the preferred method is to use Tox:

```
$ tox
```

The previous call would run `tox` for different Python versions,
checks the source code for errors, and builds the documentation.

If you want to see the target, use the option `-l` to print a list:

```
$ tox -l
```

To only run a special target, use the `-e` option. The following
example runs the test cases for the 3.4 interpreter only:

```
$ tox -e 3.4
```

## Packaging and Versioning

The version schema is based on `bumpversion` and follows the
standard rules as shown below.

* For backwards-compatible bug fixes

```
$ bumpversion patch
```

* For additional functionality in a backwards-compatible manner.
  When changed set the patch level back to zero

```
$ bumpversion minor
```

* For incompatible API changes. When changed set the patch and minor
  level back to zero

```
$ bumpversion major
```

The creation of RPM package sources has to be done by calling
the following make target:

```
$ make build
```

The sources are collected below the `dist/` directory. In there you
will find all required files to submit a package to the Open Build
Service or just build it with `rpmbuild`.


## Documentation

The documentation is implemented as manual pages based on Sphinx
using the ReST markup. In order to build the manual pages for testing
just call:

```
$ cd doc
$ make man
```
