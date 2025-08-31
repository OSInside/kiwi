#!/bin/bash

type getarg >/dev/null 2>&1 || . /lib/dracut-lib.sh

# URI pattern Based on https://tools.ietf.org/html/rfc3986#appendix-B
# with additional sub-expressions to split authority into
# userinfo, host and port
readonly URI_REGEX='^(([^:/?#]+):)?(//((([^:/?#]+)@)?([^:/?#]+)(:([0-9]+))?))?(/([^?#]*))(\?([^#]*))?(#(.*))?'

function fetch_file {
    local source_url=$1
    local source_uncompressed_bytes=$2
    local fetch_info=/tmp/fetch.info
    local fetch
    local curl_options
    local dolly_options
    curl_options=$(getarg rd.kiwi.install.pxe.curl_options=)
    dolly_options=$(getarg rd.kiwi.install.pxe.dolly_options=)
    if [ -n "${curl_options}" ]; then
        curl_options=$(str_replace "${curl_options}" "," " ")
        fetch="curl ${curl_options} -f ${source_url}"
    else
        fetch="curl -f ${source_url}"
    fi
    if [ -n "${dolly_options}" ]; then
        dolly_options=$(str_replace "${dolly_options}" "," " ")
        fetch="dolly ${dolly_options} -f ${source_url}"
    fi
    if _is_dolly "${source_url}";then
        fetch="dolly"
    fi
    if _is_xz_compressed "${source_url}";then
        fetch="${fetch} | xz -d"
    fi
    if [ -z "${source_uncompressed_bytes}" ];then
        eval "${fetch}" 2>${fetch_info}
    else
        eval "${fetch}" 2>${fetch_info} |\
            pv --size "${source_uncompressed_bytes}" --stop-at-size -n
    fi
    return "${PIPESTATUS[0]}"
}

function uri_scheme {
    [[ "$*" =~ ${URI_REGEX} ]] && echo "${BASH_REMATCH[2]}"
}

function uri_authority {
    [[ "$*" =~ ${URI_REGEX} ]] && echo "${BASH_REMATCH[4]}"
}

function uri_user {
    [[ "$*" =~ ${URI_REGEX} ]] && echo "${BASH_REMATCH[6]}"
}

function uri_host {
    [[ "$*" =~ ${URI_REGEX} ]] && echo "${BASH_REMATCH[7]}"
}

function uri_port {
    [[ "$*" =~ ${URI_REGEX} ]] && echo "${BASH_REMATCH[9]}"
}

function uri_path {
    [[ "$*" =~ ${URI_REGEX} ]] && echo "${BASH_REMATCH[10]}"
}

function uri_relative_path {
    [[ "$*" =~ ${URI_REGEX} ]] && echo "${BASH_REMATCH[11]}"
}

function uri_query {
    [[ "$*" =~ ${URI_REGEX} ]] && echo "${BASH_REMATCH[13]}"
}

function uri_fragment {
    [[ "$*" =~ ${URI_REGEX} ]] && echo "${BASH_REMATCH[15]}"
}

#======================================
# Methods considered private
#--------------------------------------
function _is_xz_compressed {
    local source_url=$1
    [[ ${source_url} =~ .xz$ ]]
}

function _is_dolly {
    local source_url=$1
    [[ ${source_url} =~ ^dolly ]]
}
