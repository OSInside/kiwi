#!/bin/bash
# git clone https://github.com/OSInside/kiwi.git
# Simple build test script to build the integration test
# images from a given test directory. The host to run this
# command requires the following tools:
#
# - tree
# - git
# - xmllint
# - podman
# - pip
#
# And requires the installation of the kiwi box plugin
#
# $ pip install --upgrade kiwi-boxed-plugin
#
set -e

ARGUMENT_LIST=(
    "test-dir:"
    "test-name:"
    "box-name:"
    "vm"
)

function usage() {
    echo "usage: build-tests --test-dir <dir>"
    echo "  --test-dir <dir>"
    echo "    Some test dir name, e.g. build-tests/x86/tumbleweed/"
    echo "  --test-name <name>"
    echo "    some test name, e.g. test-image-disk"
    echo "  --box-name <name>"
    echo "    name of the box to use for the build, default: universal"
    echo "  --vm"
    echo "    build in a virtual machine instead of a container"
}

if ! opts=$(getopt \
    --longoptions "$(printf "%s," "${ARGUMENT_LIST[@]}")" \
    --name "$(basename "$0")" \
    --options "" \
    -- "$@"
); then
    usage
    exit 0
fi

eval set --"${opts}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --test-dir)
            argTestDir=$2
            shift 2
            ;;

        --test-name)
            argTestName=$2
            shift 2
            ;;

        --box-name)
            argBoxName=$2
            shift 2
            ;;

        --vm)
            argVM=1
            shift
            ;;

        *)
            break
            ;;
    esac
done

if [ ! "${argTestDir}" ];then
    usage
    exit 1
fi

if [ ! -e "${argTestDir}"/.repos ];then
    echo "No .repos information for specified test dir"
    exit 1
fi

boxname=universal
if [ "${argBoxName}" ];then
    boxname="${argBoxName}"
fi

function create_repo_list() {
    local build_dir=$1
    if [ -s "${build_dir}"/.repos ];then
        local repo_options="--ignore-repos"
        while read -r repo;do
            repo_options="${repo_options} --add-repo ${repo}"
        done < "${build_dir}"/.repos
        echo "${repo_options}"
    fi
}

function create_build_commands() {
    local build_dir=$1
    local test_name=$2
    build_commands=()
    for image in "${build_dir}"/*;do
        test -e "${image}/appliance.kiwi" || continue
        test -e "${image}/.skip_boxbuild_container" && continue
        base_image=$(basename "${image}")
        if [ -n "${test_name}" ] && [ ! "${test_name}" = "${base_image}" ];then
            continue
        fi
        build_command="kiwi-ng --debug"
        has_profiles=false
        repo_options=$(create_repo_list "${build_dir}")
        box_options="system boxbuild --box ${boxname}"
        if [ ! "${argVM}" = 1 ];then
            box_options="${box_options} --container"
        fi
        for profile in $(
            xmllint --xpath "//image/profiles/profile/@name" \
            "${image}/appliance.kiwi" 2>/dev/null | cut -f2 -d\"
        );do
            has_profiles=true
            target_dir="build_results/${base_image}/${profile}"
            build_command="${build_command} --profile ${profile}"
            build_command="${build_command} ${box_options} --"
            build_command="${build_command} --description $image"
            build_command="${build_command} ${repo_options}"
            build_command="${build_command} --target-dir ${target_dir}"
            echo "${build_command}" \
                > "build_results/${base_image}-${profile}.build"
            build_commands+=( "${build_command}" )
            build_command="kiwi-ng --debug"
        done
        if [ "${has_profiles}" = "false" ];then
            target_dir="build_results/${base_image}"
            build_command="${build_command} ${box_options} --"
            build_command="${build_command} --description $image"
            build_command="${build_command} ${repo_options}"
            build_command="${build_command} --target-dir ${target_dir}"
            echo "${build_command}" \
                > "build_results/${base_image}.build"
            build_commands+=( "${build_command}" )
        fi
    done
}

# create results directory
mkdir -p build_results

# build command list
create_build_commands "${argTestDir}" "${argTestName}"

# build them in a row
for build in "${build_commands[@]}";do
    ${build}
    sudo rm -rf build_results/*/*/build/
    sudo rm -rf build_results/*/build/
done

# show result tree
test -d build_results && tree -L 3 build_results
