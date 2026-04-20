#!/bin/bash

set -ex

curl https://sdk.cloud.google.com > install.sh
bash install.sh --disable-prompts --install-dir=/usr/share

ln -s /usr/share/google-cloud-sdk/bin/gcloud /usr/bin/gcloud
ln -s /usr/share/google-cloud-sdk/bin/gsutil /usr/bin/gsutil
ln -s /usr/share/google-cloud-sdk/bin/bq /usr/bin/bq
