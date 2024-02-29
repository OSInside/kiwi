#!/bin/bash

GITHUB_HEAD_REF=$1

git fetch --all
git config user.email cherrypick@action.com
git config user.name git_action
git checkout master
git log \
    --pretty=oneline \
    --no-merges origin/master..origin/"${GITHUB_HEAD_REF}" |\
cut -f1 -d " " | head -n -1 > commit.list

for i in $(tac commit.list);do
    git cherry-pick --keep-redundant-commits "$i" 2>/dev/null || (
        echo "****** SKIPPED: $i ******"
        git cherry-pick --skip
    )
done
