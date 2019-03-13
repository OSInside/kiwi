#!/bin/bash

helper/update_changelog.py --since package/python-kiwi.changes \
    > package/python-kiwi.changes && \
helper/update_changelog.py --until package/python-kiwi.changes \
    > package/python-kiwi.changes && \
git commit -S -m 'Update changelog reference' \
    package/python-kiwi.changes
