#!/bin/bash

set -ex

#======================================
# Disable password based login for ssh
#--------------------------------------
ssh_conf=/etc/ssh/sshd_config
if [ ! -e "${ssh_conf}" ];then
    ssh_conf=/usr/etc/ssh/sshd_config
fi
sed -i 's/#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' "${ssh_conf}"
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' "${ssh_conf}"
# Remove the password for root
sed -i 's/^root:[^:]*:/root:*:/' /etc/shadow
# Allow root access on serial console
grep -E -q '^ttyS0$' /etc/securetty || echo ttyS0 >> /etc/securetty

#======================================
# PROD: Remove serial autologin !
#--------------------------------------
mkdir -p /etc/systemd/system/serial-getty@ttyS0.service.d
cat << EOF > /etc/systemd/system/serial-getty@ttyS0.service.d/override.conf
[Service]
ExecStart=
ExecStart=-/usr/sbin/agetty --autologin root --noclear --keep-baud 115200,38400,9600 ttyS0 $TERM
EOF
systemctl enable serial-getty@ttyS0

#======================================
# Add a data directory
#--------------------------------------
# we will store the example enclave .eif binary here
mkdir -p /data

#======================================
# Add empty enclaves log file
#--------------------------------------
mkdir -p /var/log/nitro_enclaves
touch /var/log/nitro_enclaves/nitro_enclaves.log

#======================================
# Lazy helper /run/nitro_enclaves
#--------------------------------------
cat << EOF > /root/.bashrc
mkdir -p /run/nitro_enclaves
EOF

#======================================
# Lazy helper show-nitrotpm-pcrs
#--------------------------------------
# This is a helper script to show the PCR values from the attestation document.
# It assumes the document is stored in /tmp/nitro.attest.cbor
# nitro-tpm-attest > /tmp/nitro.attest.cbor must be run before this script
# to generate the document.
cat << EOF > /usr/bin/show-nitrotpm-pcrs
#!/usr/bin/python3
import cbor2
with open('/tmp/nitro.attest.cbor', 'rb') as doc_fd:
    data = cbor2.loads(doc_fd.read())
    # Load and decode document payload
    doc_payload = data[2]
    doc = cbor2.loads(doc_payload)
    for n in doc['nitrotpm_pcrs'].keys():
        print(f'PCR{n}: {doc['nitrotpm_pcrs'][n].hex()}')
EOF
chmod 755 /usr/bin/show-nitrotpm-pcrs

#======================================
# Lazy helper vsock_client
#--------------------------------------
cat << EOF > /usr/bin/vsock_client
#!/usr/bin/python3
import socket
import sys
VSOCK_PORT = 5000
def main():
    if len(sys.argv) != 2:
        print('Usage: python3 client.py <enclave_cid>')
        sys.exit(1)
    enclave_cid = int(sys.argv[1])
    client = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
    client.connect((enclave_cid, VSOCK_PORT))
    message = 'Hello from parent instance!'
    print(f'[Parent] Sending: {message}')
    client.sendall(message.encode())
    data = client.recv(8192)
    print(f'[Parent] Received: {data.decode()}')
    client.close()
if __name__ == '__main__':
    main()
EOF
chmod 755 /usr/bin/vsock_client

#======================================
# Enclave allocator setup
#--------------------------------------
cat << EOF > /etc/nitro_enclaves/allocator.yaml
---
memory_mib: 2048
cpu_count: 2
EOF

#======================================
# Make sure nitro_enclaves is loaded
#--------------------------------------
cat << EOF > /etc/modules-load.d/nitro-enclaves.conf
nitro_enclaves
EOF

#======================================
# Activate Nitro allocator
#--------------------------------------
systemctl enable nitro-enclaves-allocator.service

#======================================
# Readonly ESP
#--------------------------------------
cat << EOF > /etc/fstab.script
#!/bin/bash
sed -i 's|/boot/efi vfat defaults|/boot/efi vfat ro,nosuid,nodev,noexec,noatime|g' /etc/fstab
EOF
chmod 755 /etc/fstab.script

#======================================
# Setup nitro limits
#--------------------------------------
mkdir -p /etc/systemd/system.conf.d
cat << EOF > /etc/systemd/system.conf.d/50-limits.conf
[Manager]
DefaultLimitSTACK=10240K:10240K
DefaultLimitNPROC=infinity:infinity
DefaultLimitMEMLOCK=infinity:infinity
DefaultLimitNOFILE=65535:65535
DefaultLimitSIGPENDING=30446:30446
EOF

#======================================
# Setup chrony
#--------------------------------------
mkdir -p /etc/chrony.d
cat << EOF > /etc/chrony.d/10-disable-cmdport.conf
cmdport 0
EOF

#======================================
# Setup services
#--------------------------------------
for service in \
    sshd \
    chronyd \
    cloud-init-local \
    cloud-init \
    cloud-config \
    cloud-final \
    amazon-ssm-agent \
    systemd-networkd \
    systemd-resolved
do
    systemctl enable "${service}"
done

#======================================
# Masked services
#--------------------------------------
systemctl mask systemd-boot-random-seed.service

#======================================
# Register aws
#--------------------------------------
mkdir -p /usr/share/flakes
chmod 777 /usr/share/flakes
flake-ctl podman register \
    --app /usr/bin/aws \
    --container docker.io/amazon/aws-cli \
    --target / \
    --opt "\--interactive" \
    --opt "\--security-opt label=disable" \
    --opt "\--volume %HOME:/root" \
    --opt "\--volume /var/lib/ca-certificates:/var/lib/ca-certificates" \
    --opt "\-e HOME=/root"
