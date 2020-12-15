#!/bin/bash

set -eu

# setup variables
access_token=$1
user_name=$2
user_mail=$3

repo_uri="https://x-access-token:${access_token}@github.com/OSInside/kiwi.git"
remote_name="origin"
target_branch="gh-pages"

# set git user and email
git config user.name "${user_name}"
git config user.email "${user_mail}"

# build kiwi documentation suitable for github pages
tox -e doc_gh_pages

# preserve the new docs
mv doc/build_gh_pages /tmp

# checkout current pages and wipe them completely
git checkout "${target_branch}"
git clean -f .
git rm -rf .

# sync(move) the new docs to the right place in the git
rsync -a /tmp/build_gh_pages/ .
rm -rf /tmp/build_gh_pages

# add all doc sources
git add .

# commit the new docs
if ! git commit -m "Update GitHub Pages"; then
    echo "nothing to commit"
    exit 0
fi

# force push the new docs to the pages branch
git remote set-url "${remote_name}" "${repo_uri}"
git push --force-with-lease "${remote_name}" "${target_branch}"
