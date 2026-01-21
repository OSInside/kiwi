#!/bin/bash
set -ex

mkdir -p /root/ai

curl -fsSL https://opencode.ai/install > opencode.install.sh
bash opencode.install.sh
