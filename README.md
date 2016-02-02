# KIWI—Next Generation

[![Build Status](https://travis-ci.org/SUSE/kiwi.svg?branch=master)](https://travis-ci.org/SUSE/kiwi)
[![Health](https://landscape.io/github/SUSE/kiwi/master/landscape.svg?style=flat)](https://landscape.io/github/SUSE/kiwi/master)

This is a rewrite of the current KIWI appliance builder which
you can find here: https://github.com/openSUSE/kiwi.

## Contents

  * [Status](#status)
  * [Motivation](#motivation)
  * [Supported Distributions](#supported_distributions)
  * [Contributing](#contributing)
  * [Packaging and Versioning](#packaging_and_versioning)
  
## Status

**Development Status: 4 - Beta(no release yet)**

This project is in an early development phase and some parts
of the old KIWI version are not yet available in the new
code base. If you are missing a feature at the time of the
first release don't hesitate to open an issue to allow for
a planing and implementing phase.

## Motivation

During the last years KIWI has evolved a lot. Many features were
added, even some which are not in use anymore because new technologies
made them obsolete. There is a lot of legacy code in KIWI to support
older distributions too. In order to become free from legacy code
the decision to provide a new version which can co-exist with the
existing implementation was made.

However, the current design and the lack of tests in core parts of the
current code basically prevents a major refactoring as I see it required.
Because of that, a rewrite of KIWI with a stable version in the background
seems to be the best way.

Users will be able to use both versions in parallel. Also the new
KIWI will be 100% compatible with the current format of the image
description. This means, you can build an image from the same image
description with the old and the new KIWI if the new KIWI supports
the distribution and all features the image description has
configured.

## Supported Distributions

This version of KIWI is targeted to build appliances for distributions
which are equal or newer compared to the following list:

* SUSE Linux Enterprise 12
* Red Hat Enterprise 7
* Fedora 22
* openSUSE 13.2
* SUSE Leap 42
* SUSE Tumbleweed

For anything older please consider to use the old version

## Contributing

The core appliance builder is developed in Python and follows the
test driven development rules. The XML, schema, and stylesheets are
taken from the old version of KIWI. Also the entire boot code
(written in bash) is taken from the old KIWI codebase.

The Python project uses `virtualenv` to setup a development
environment for the desired Python version. The following procedure
describes how to create such an environment for Python 2.7. Although
it's targetted for openSUSE, it's very similar for other distributions
with minor corrections:

```
$ sudo zypper in python-virtualenv
$ sudo zypper in python-bumpversion

$ virtualenv-2.7 .env2
```

Once the development environment exists it needs to be activated
and initialized with the project required Python modules:

```
$ . .env2/bin/activate

$ pip install -r .virtualenv.dev-requirements.txt

$ ./setup.py develop
```

The __develop__ target of the `setup.py` script automatically creates
the application entry point called __kiwi__, which allows to simply
call the application from the current code base

```
$ kiwi --help
```

In order to leave the development mode just call

```
$ deactivate
```

## Packaging and Versioning

The version schema is based on python-bumpversion and follows the
standard rules as shown below.

```
$ bumpversion [patch | minor | major]
```

The creation of rpm package sources has to be done by calling
the following make target:

```
$ make build
```

The sources are collected below the `dist/` directory. In there you
will find all required files to submit a package to the open build
service or just build it with rpmbuild
