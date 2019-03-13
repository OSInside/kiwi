#!/bin/bash

if [ -z "$*" ]; then
    echo 'usage: bumpversion.sh major|minor|patch'
    exit 1
fi

helper/update_changelog.py package/python-kiwi.changes \
    > package/python-kiwi.changes.new && \
cat package/python-kiwi.changes \
    >> package/python-kiwi.changes.new && \
mv package/python-kiwi.changes.new \
    package/python-kiwi.changes && \
git commit -S -m 'Update changelog reference' \
    package/python-kiwi.changes && \
sleep 2 && bumpversion "$@"
