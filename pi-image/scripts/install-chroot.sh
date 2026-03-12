#!/bin/bash -e
# Runs inside the aarch64 chroot on the Pi image rootfs.
# Called via: sudo chroot /mnt/pi /bin/bash /tmp/install-chroot.sh

apt-get update -qq
apt-get install -y --no-install-recommends \
  python3-venv python3-pip python3-psycopg2 libpq5

python3 -m pip install --no-cache-dir --break-system-packages uv

# Create the byteorder user with a locked password. Auto-assign UID so we
# don't collide with any existing UID-1000 user (e.g. a default 'pi' user).
# Any UID >= 1000 user is enough to suppress Pi OS's first-boot username wizard.
useradd --create-home --shell /bin/bash --groups dialout byteorder
passwd -l byteorder

# Fix ownership now that the user exists
chown -R byteorder:byteorder /opt/byteorder-print
chown -R byteorder:byteorder /etc/byteorder

uv venv --system-site-packages /opt/byteorder-print/venv

/opt/byteorder-print/venv/bin/uv pip install --no-cache-dir \
  -r /opt/byteorder-print/requirements-pi.txt

# Disable the first-boot username wizard; enable SSH
systemctl disable userconfig || true
systemctl enable ssh
systemctl enable byteorder-print.service
