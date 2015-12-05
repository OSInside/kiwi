# KIWI - next generation

[![Build Status](https://travis-ci.org/SUSE/kiwi.svg?branch=master)](https://travis-ci.org/SUSE/kiwi)
[![Health](https://landscape.io/github/SUSE/kiwi/master/landscape.svg?style=flat)](https://landscape.io/github/SUSE/kiwi/master)

This is a rewrite of the current kiwi appliance builder which
you can find here: https://github.com/openSUSE/kiwi.

## Contents

  * [Status](#status)
  * [Motivation](#motivation)
  * [Supported Distributions](#supported_distributions)
  * [Development](#development)
  
## Status

Development - no release yet

This project is in an early development phase and some parts
the old kiwi version can do are not yet available in the new
code base. If you are missing a feature at the time of the
first release don't hesitate to open an issue such that I
can collect them. Of course external contributions are very
much appreciated.

## Motivation

During the last years kiwi has evolved a lot, many features were
added, even some which are not in use anymore because new technologies
made them obsolete. There is a lot of legacy code in kiwi to support
older distributions too. I'd like to get rid of all of these and come
back to a clean appliance building system.

However the current design and the lack of tests in core parts of the
code prevents us from major refactoring as I see them required. Because
of that a rewrite of kiwi with a stable version in the background
seems to be the best way.

Users will be able to use both versions in parallel. Also the new
kiwi will be 100% compatible with the current format of the image
description, which means you can build an image from the same image
description with the old and the new kiwi if the new kiwi supports
the distribution and all features the image description has
configured

## Supported Distributions

This version of kiwi is targeted to build appliances for distributions
which are equal or newer compared to the following list:

* SUSE Linux Enterprise 12
* Red Hat Enterprise 7
* Fedora 23
* openSUSE 13.2
* SUSE Leap 42
* SUSE Tumbleweed

For anything older please consider to use the old version

## Development

The appliance builder part is developed in python and follows the
test driven development rules. The XML, schema and stylesheets are
taken from the old version of kiwi. Also the entire boot code
written in bash is taken over from the old kiwi codebase.
