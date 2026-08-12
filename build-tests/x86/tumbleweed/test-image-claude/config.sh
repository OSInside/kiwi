#!/bin/bash
set -ex

mkdir -p /root/ai

zypper ar -f https://packages.cloud.google.com/yum/repos/cloud-sdk-el10-x86_64 google-cloud-rhel10

zypper ar -f https://download.opensuse.org/tumbleweed/repo/oss TW

zypper --non-interactive --gpg-auto-import-keys in --auto-agree-with-licenses --allow-vendor-change google-cloud-cli

npm install -g @anthropic-ai/claude-code

mkdir -p ~/.claude

touch ~/.claude/settings.json
