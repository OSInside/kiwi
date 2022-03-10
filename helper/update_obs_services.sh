#!/bin/bash

set -euo pipefail

api_target="https://api.opensuse.org/trigger/runservice"
api_token=$1

while read -r build_test; do
    build_test_path=$(dirname "${build_test}")
    dist=$(echo "${build_test_path}" | cut -f 3 -d/)
    arch=$(echo "${build_test_path}" | cut -f 2 -d/)
    project="Virtualization:Appliances:Images:Testing_${arch}:${dist}"
    package=$(basename "${build_test_path}")
    curl_target="${api_target}?project=${project}&package=${package}"

    echo "Updating Test: ${package} for: ${project}"
    curl -H "Authorization: Token ${api_token}" \
        -X POST "${curl_target}"
done < <(find build-tests -name "appliance.kiwi")
