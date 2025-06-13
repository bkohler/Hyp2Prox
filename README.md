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
2. Stops the specified VM and exports it to a given path (or uses Change Block Tracking for warm migration).
3. Converts the exported VHDX to QCOW2 using `virt-v2v` (which injects virtio drivers).
4. Creates a new VM on Proxmox via its API.
5. Imports the converted disk and attaches it as a virtio disk.
6. Starts the VM on Proxmox.

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
  --warm
```

Adjust the parameters to match your environment (storage, export paths, etc.).

### Warm migration of a Windows VM

The `--warm` option performs an incremental migration using Change Block Tracking.
This keeps the VM running while the base disk is copied and only requires a
final shutdown to capture the changes.

1. Ensure the VM is running on Hyper‑V and that you have a directory on the host
   where exports can be written (e.g. `C:\temp\export`).
2. Run the script with the `--warm` flag:

   ```bash
   python migrate_vm.py \
     --hyperv-host hyperv.example.local \
     --hyperv-user Administrator \
     --hyperv-pass secret \
     --proxmox-host proxmox.local \
     --proxmox-user root@pam \
     --proxmox-pass secret \
     --proxmox-node pve01 \
     --vm-name WinVM \
     --vmid 200 \
     --warm
   ```
3. The script enables CBT, exports the base disk while the VM continues running
   and converts it to QCOW2.
4. A VM with the specified `vmid` is created on Proxmox and the base disk is
   imported.
5. The VM is briefly stopped on Hyper‑V so that the script can export only the
   changed blocks, merge them with the base, and update the disk on Proxmox.
6. Finally the VM is started on Proxmox and Change Block Tracking is disabled on
   Hyper‑V.

With this workflow the downtime is limited to the final export of changed
blocks and the import on Proxmox.
