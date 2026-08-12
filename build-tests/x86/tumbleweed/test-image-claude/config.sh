#!/bin/bash
set -ex

zypper ar -f https://download.opensuse.org/tumbleweed/repo/oss TW

npm install -g @anthropic-ai/claude-code

curl https://sdk.cloud.google.com > install.sh
bash install.sh --disable-prompts --install-dir=/usr/share

ln -s /usr/share/google-cloud-sdk/bin/gcloud /usr/bin/gcloud
ln -s /usr/share/google-cloud-sdk/bin/gsutil /usr/bin/gsutil
ln -s /usr/share/google-cloud-sdk/bin/bq /usr/bin/bq

mkdir -p /etc/claude-code

cat > /etc/claude-code/managed-settings.json <<'EOF'
{
  "permissions": {
    "defaultMode": "default"
  },
  "env": {
    "CLAUDE_CODE_USE_VERTEX": "1",
    "CLOUD_ML_REGION": "global",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-5",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4-5@20251001"
  }
}
EOF
chmod 0644 /etc/claude-code/managed-settings.json