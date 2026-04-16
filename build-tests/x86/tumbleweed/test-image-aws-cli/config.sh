#!/bin/bash
set -ex

rm -f awscliv2.zip
rm -rf aws

# latest fails with a core dump on s2n_init()
#curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-2.13.33.zip" -o "awscliv2.zip"

unzip awscliv2.zip

./aws/install --bin-dir /usr/bin --install-dir /usr/share/aws-cli

rm -f awscliv2.zip
rm -rf aws
