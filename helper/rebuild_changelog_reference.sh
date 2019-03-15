#!/bin/bash

git log --no-merges --format=fuller > package/python-kiwi.changes

git commit -S -m 'Update changelog reference' \
    package/python-kiwi.changes
