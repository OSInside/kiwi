import pytest


ZYPPER_IN_CMD = "zypper -n in openssh sudo && /usr/sbin/sshd-gen-keys-start"


@pytest.mark.parametrize(
    "container_per_test,install_cmd",
    (
        ("Tumbleweed", ZYPPER_IN_CMD),
        ("Leap-15.2", ZYPPER_IN_CMD),
        ("Leap-15.3", ZYPPER_IN_CMD),
        ("centos:stream8", "yum -y install openssh-server sudo && /usr/libexec/openssh/sshd-keygen ed25519")
    ),
    indirect=["container_per_test"],
)
def test_configures_system_for_vagrant(container_per_test, install_cmd):
    # unfortunately we have to do a bit of setup for vagrant
    container_per_test.run_expect([0], install_cmd)
    container_per_test.run_expect(
        [0], "groupadd vagrant && useradd -g vagrant vagrant"
    )

    container_per_test.run_expect(
        [0],
        r"""cat <<EOF > /usr/bin/systemctl
#!/bin/bash
printf "%s " "\$@" >> /systemctl_params
echo >> /systemctl_params
EOF
chmod +x /usr/bin/systemctl
""",
    )

    container_per_test.run_expect(
        [0], ". /bin/functions.sh && baseVagrantSetup"
    )

    # check vagrant user's ssh config
    dot_ssh = container_per_test.file("/home/vagrant/.ssh")
    assert dot_ssh.is_directory
    assert dot_ssh.group == "vagrant"
    assert dot_ssh.user == "vagrant"
    assert dot_ssh.mode == 0o700

    authorized_keys = container_per_test.file(
        "/home/vagrant/.ssh/authorized_keys"
    )
    assert authorized_keys.is_file
    assert authorized_keys.group == "vagrant"
    assert authorized_keys.user == "vagrant"
    assert authorized_keys.mode == 0o600
    assert "vagrant insecure public key" in authorized_keys.content_string

    # check the sshd config
    sshd_config = container_per_test.run_expect([0], "sshd -T")
    assert "UseDNS no".lower() in sshd_config.stdout
    assert "GSSAPIAuthentication no".lower() in sshd_config.stdout

    # check that the shared /vagrant folder is present and has the correct permissions
    vagrant_shared_dir = container_per_test.file("/vagrant")
    assert vagrant_shared_dir.is_directory
    assert vagrant_shared_dir.group == "vagrant"
    assert vagrant_shared_dir.user == "vagrant"

    vagrant_sudoers = container_per_test.file("/etc/sudoers.d/vagrant")
    if vagrant_sudoers.exists and vagrant_sudoers.is_file:
        assert (
            vagrant_sudoers.content_string.strip() == "vagrant ALL=(ALL) NOPASSWD: ALL"
        )
        assert vagrant_sudoers.mode == 0o440
        assert vagrant_sudoers.user == "root"
        assert vagrant_sudoers.group == "root"
    else:
        sudoers = container_per_test.file("/etc/sudoers")
        assert sudoers.exists and sudoers.is_file
        assert "vagrant ALL=(ALL) NOPASSWD: ALL" in sudoers.content_string

    # check that systemctl was called enabling sshd
    assert (
        "enable sshd"
        in container_per_test.file("/systemctl_params").content_string
    )
