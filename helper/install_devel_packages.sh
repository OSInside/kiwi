#!/bin/bash

source /etc/os-release

case ${ID} in
    fedora|centos|rhel)
        dnf --setopt=install_weak_deps=False install \
            python3 python3-devel 'python3dist(pip)' \
            'python3dist(tox)' make gcc which xz xorriso libxml2-devel \
            libxslt-devel enchant enchant-devel genisoimage ShellCheck \
            latexmk texlive-cmap texlive-metafont texlive-ec libffi-devel \
            texlive-babel-english texlive-fncychap texlive-fancyhdr \
            texlive-titlesec texlive-tabulary texlive-framed texlive-wrapfig \
            texlive-parskip texlive-upquote texlive-capt-of texlive-needspace \
            texlive-makeindex texlive-times texlive-helvetic texlive-courier \
            texlive-gsftopk texlive-updmap-map texlive-dvips
    ;;
    opensuse-*|sles)
        zypper install --no-recommends \
            python3-devel python3-tox libxml2-devel libxslt-devel glibc-devel \
            gcc xorriso texlive-fncychap texlive-wrapfig texlive-capt-of \
            texlive-latexmk texlive-cmap texlive-babel-english \
            texlive-times texlive-titlesec texlive-tabulary texlive-framed \
            texlive-float texlive-upquote texlive-parskip texlive-needspace \
            texlive-makeindex-bin texlive-collection-fontsrecommended \
            texlive-psnfss libffi-devel enchant-devel
    ;;
    *)
        echo "Unknown distribution: ${os}"
    ;;
esac
