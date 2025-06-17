---
marp: true
title: Hyp2Prox - Hyper-V to Proxmox Migration
---

# Hyp2Prox

**Simple VM migration from Hyper-V to Proxmox**

---

## Requirements

- Python 3.10+
- `proxmoxer` and `pywinrm`
- `virt-v2v` tool
- Proxmox command line tools (`qm`)

---

## Basic Workflow

1. Stop VM on Hyper-V
2. Export VM disk
3. Convert VHDX to QCOW2
4. Create VM on Proxmox
5. Import disk and start VM

---

## Warm Migration Option

- Uses Change Block Tracking (CBT)
- Copies base disk while VM keeps running
- Final shutdown exports only changed blocks
- Minimizes downtime

---

## Example Command

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
  --vmid 100
```

Add `--warm` for incremental migration.

---

## Warm Migration Steps

1. Enable CBT on Hyper-V
2. Export base disk
3. Convert and import to Proxmox
4. Stop VM and export changes
5. Merge delta, convert, update disk
6. Start VM on Proxmox

---

# Questions?

---
