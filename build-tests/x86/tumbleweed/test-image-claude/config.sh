#!/bin/bash
set -ex

mkdir -p /root/ai

echo 'export PATH=/root/.claude/bin:$PATH' > /root/.bashrc 

curl -fsSL https://claude.ai/install.sh > claude.install.sh
bash claude.install.sh

test -d /root/.claude
