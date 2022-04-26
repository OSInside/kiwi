from pytest_container.container import DerivedContainer
from .conftest import (
    CONTAINERS_WITH_YUM,
    CONTAINERS_WITH_ZYPPER,
)
import pytest


VAGRANT_SETUP_CONTAINERFILE = r"""RUN groupadd vagrant && useradd -g vagrant vagrant
RUN echo $'#!/bin/bash \n\
printf "%s " "$@" >> /systemctl_params \n\
echo >> /systemctl_params \n\
'> /usr/bin/systemctl && chmod +x /usr/bin/systemctl
"""

ZYPPER_IN_CMD_CONTAINERFILE = (
    """RUN zypper -n in openssh sudo && /usr/sbin/sshd-gen-keys-start
""" + VAGRANT_SETUP_CONTAINERFILE
)


@pytest.mark.parametrize(
    "container_per_test",
    [
        DerivedContainer(base=cont, containerfile=ZYPPER_IN_CMD_CONTAINERFILE)
        for cont in CONTAINERS_WITH_ZYPPER
    ] + [
        DerivedContainer(
            base=cont,
            containerfile="""RUN yum -y install openssh-server sudo && /usr/libexec/openssh/sshd-keygen ed25519
""" + VAGRANT_SETUP_CONTAINERFILE,
        )
        for cont in CONTAINERS_WITH_YUM
    ],
    indirect=["container_per_test"],
)
def test_configures_system_for_vagrant(container_per_test):
    container_per_test.connection.run_expect(
        [0], ". /bin/functions.sh && baseVagrantSetup"
    )

    # check vagrant user's ssh config
    dot_ssh = container_per_test.connection.file("/home/vagrant/.ssh")
    assert dot_ssh.is_directory
    assert dot_ssh.group == "vagrant"
    assert dot_ssh.user == "vagrant"
    assert dot_ssh.mode == 0o700

    authorized_keys = container_per_test.connection.file(
        "/home/vagrant/.ssh/authorized_keys"
    )
    assert authorized_keys.is_file
    assert authorized_keys.group == "vagrant"
    assert authorized_keys.user == "vagrant"
    assert authorized_keys.mode == 0o600
    assert "vagrant insecure public key" in authorized_keys.content_string

    # check the sshd config
    sshd_config = container_per_test.connection.run_expect([0], "sshd -T").stdout
    assert "UseDNS no".lower() in sshd_config
    assert "GSSAPIAuthentication no".lower() in sshd_config

    # check that the shared /vagrant folder is present and has the correct permissions
    vagrant_shared_dir = container_per_test.connection.file("/vagrant")
    assert vagrant_shared_dir.is_directory
    assert vagrant_shared_dir.group == "vagrant"
    assert vagrant_shared_dir.user == "vagrant"

    vagrant_sudoers = container_per_test.connection.file(
        "/etc/sudoers.d/vagrant"
    )
    if vagrant_sudoers.exists and vagrant_sudoers.is_file:
        assert (
            vagrant_sudoers.content_string.strip() == "vagrant ALL=(ALL) NOPASSWD: ALL"
        )
        assert vagrant_sudoers.mode == 0o440
        assert vagrant_sudoers.user == "root"
        assert vagrant_sudoers.group == "root"
    else:
        sudoers = container_per_test.connection.file("/etc/sudoers")
        assert sudoers.exists and sudoers.is_file
        assert "vagrant ALL=(ALL) NOPASSWD: ALL" in sudoers.content_string

    # check that systemctl was called enabling sshd
    assert (
        "enable sshd"
        in container_per_test.connection.file(
            "/systemctl_params"
        ).content_string
    )
