#!/bin/bash
set -ex

mkdir -p /root/ai

npm install -g @anthropic-ai/claude-code

zypper ar -f https://packages.cloud.google.com/yum/repos/cloud-sdk-el10-x86_64 google-cloud-rhel10

zypper ar  https://download.opensuse.org/tumbleweed/repo/oss TW

zypper in google-cloud-cli

mkdir -p ~/.claude

cat > ~/.claude/settings.json <<'EOF'
{
  "permissions": {
    "defaultMode": "default"
  },
  "env": {
    "CLAUDE_CODE_USE_VERTEX": "1",
    "CLOUD_ML_REGION": "global",
    "ANTHROPIC_VERTEX_PROJECT_ID": "your_project_id",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-5",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4-5@20251001"
  }
}
EOF
chmod 0644 ~/.claude/settings.json
