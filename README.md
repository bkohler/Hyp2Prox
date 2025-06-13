# Hyp2Prox

This repository provides a simple Python script to migrate virtual machines from a Hyper-V cluster to a Proxmox cluster using their respective APIs.

## Requirements

- Python 3.10+
- `proxmoxer` and `pywinrm` Python packages
- `virt-v2v` tool installed on the machine running the script
- Proxmox command line tools (`qm`)

Install dependencies with:

```bash
pip install proxmoxer pywinrm
```

## Usage

The `migrate_vm.py` script performs the following steps:

1. Connects to the Hyper-V host via WinRM.
2. Stops the specified VM and exports it to a given path.
3. Converts the exported VHDX to QCOW2 using `virt-v2v` (which injects virtio drivers).
4. Creates a new VM on Proxmox via its API.
5. Imports the converted disk and attaches it as a virtio disk.
6. Sets up a virtio network interface and boot order.
7. Optionally mounts the `virtio-win` ISO for Windows guests.
8. Starts the VM on Proxmox.

Example invocation:

```bash
python migrate_vm.py \
  --hyperv-host hyperv.example.local \
  --hyperv-user Administrator \
  --hyperv-pass secret \
  --proxmox-host proxmox.local \
  --proxmox-user root@pam \
  --proxmox-pass secret \
  --proxmox-node pve01 \
  --vm-name MyVM \
  --vmid 100 \
  --windows
```

Adjust the parameters to match your environment (storage, export paths, etc.).
