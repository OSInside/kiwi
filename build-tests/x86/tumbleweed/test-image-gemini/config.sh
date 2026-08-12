#!/bin/bash
set -ex

mkdir -p /root/ai

# shellcheck disable=SC2016
echo 'export PATH=/root/.antigravity/bin:/root/.local/bin:$PATH' > /root/.bashrc

# shellcheck disable=SC2016
echo 'export PATH=/root/.antigravity/bin:/root/.local/bin:$PATH' >> /etc/bash.bashrc

# shellcheck disable=SC1091
source /root/.bashrc

# install antigravity
curl -fsSL https://antigravity.google/cli/install.sh > antigravity.install.sh
bash antigravity.install.sh

# install gemini-cli
npm install -g @google/gemini-cli@nightly
