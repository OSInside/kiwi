#!/bin/bash
set -ex

mkdir -p /root/ai

echo 'export PATH=/root/.antigravity/bin:/root/.local/bin:$PATH' > /root/.bashrc
echo 'export PATH=/root/.antigravity/bin:/root/.local/bin:$PATH' >> /etc/bash.bashrc
source /root/.bashrc

# install antigravity
curl -fsSL https://antigravity.google/cli/install.sh > antigravity.install.sh
bash antigravity.install.sh

# install gemini-cli
npm install -g @google/gemini-cli@nightly
