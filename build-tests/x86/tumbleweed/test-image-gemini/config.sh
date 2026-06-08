#!/bin/bash
set -ex

mkdir -p /root/ai

echo 'export PATH=/root/.antigravity/bin:/root/.local/bin:$PATH' > /root/.bashrc
source /root/.bashrc

curl -fsSL https://antigravity.google/cli/install.sh > antigravity.install.sh

bash antigravity.install.sh
