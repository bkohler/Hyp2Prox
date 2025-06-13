#!/usr/bin/env python3

"""Simple VM migration script from Hyper-V to Proxmox via API."""

import argparse
import os
import subprocess
from dataclasses import dataclass

import winrm
from proxmoxer import ProxmoxAPI


@dataclass
class HyperVCredentials:
    host: str
    username: str
    password: str


def run_ps(session: winrm.Session, script: str) -> None:
    """Run a PowerShell script on the remote host and fail on errors."""
    result = session.run_ps(script)
    if result.status_code != 0:
        raise RuntimeError(result.std_err)


class HyperVCluster:
    """Handle Hyper-V operations via WinRM."""

    def __init__(self, creds: HyperVCredentials) -> None:
        self.session = winrm.Session(creds.host, auth=(creds.username, creds.password))

    def stop_vm(self, name: str) -> None:
        run_ps(self.session, f"Stop-VM -Name '{name}' -Force")

    def export_vm(self, name: str, path: str) -> None:
        run_ps(self.session, f"Export-VM -Name '{name}' -Path '{path}' -Force")


class ProxmoxCluster:
    """Wrapper around Proxmox API calls used during migration."""

    def __init__(self, host: str, user: str, password: str, verify_ssl: bool = False):
        self.api = ProxmoxAPI(host, user=user, password=password, verify_ssl=verify_ssl)

    def create_vm(self, node: str, vmid: int, name: str, cores: int, memory: int) -> None:
        self.api.nodes(node).qemu.post(vmid=vmid, name=name, cores=cores, memory=memory)

    def import_disk(self, node: str, vmid: int, image_path: str, storage: str) -> None:
        subprocess.check_call([
            'qm', 'importdisk', str(vmid), image_path, storage, '--node', node
        ])

    def set_virtio_disk(self, node: str, vmid: int, storage: str) -> None:
        self.api.nodes(node).qemu(vmid).config.post(
            virtio0=f"{storage}:vm-{vmid}-disk-0"
        )

    def start_vm(self, node: str, vmid: int) -> None:
        self.api.nodes(node).qemu(vmid).status.start.post()


def convert_disk(vhdx_path: str, qcow_path: str) -> None:
    """Convert a VHDX disk to QCOW2 with virt-v2v for driver injection."""
    subprocess.check_call([
        'virt-v2v', '-i', 'disk', vhdx_path,
        '-o', 'local', '-os', os.path.dirname(qcow_path),
        '-of', 'qcow2', qcow_path
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate a VM from Hyper-V to Proxmox")
    parser.add_argument('--hyperv-host', required=True)
    parser.add_argument('--hyperv-user', required=True)
    parser.add_argument('--hyperv-pass', required=True)
    parser.add_argument('--proxmox-host', required=True)
    parser.add_argument('--proxmox-user', required=True)
    parser.add_argument('--proxmox-pass', required=True)
    parser.add_argument('--proxmox-node', required=True)
    parser.add_argument('--vm-name', required=True)
    parser.add_argument('--vmid', type=int, required=True)
    parser.add_argument('--cores', type=int, default=2)
    parser.add_argument('--memory', type=int, default=2048)
    parser.add_argument('--export-path', default='C:\\temp\\export')
    parser.add_argument('--storage', default='local-lvm')
    parser.add_argument('--qcow-path', default='/var/tmp/converted.qcow2')
    args = parser.parse_args()

    hyperv = HyperVCluster(HyperVCredentials(args.hyperv_host, args.hyperv_user, args.hyperv_pass))
    proxmox = ProxmoxCluster(args.proxmox_host, args.proxmox_user, args.proxmox_pass)

    print('Stopping VM on Hyper-V...')
    hyperv.stop_vm(args.vm_name)

    print('Exporting VM...')
    hyperv.export_vm(args.vm_name, args.export_path)
    vhdx_path = os.path.join(args.export_path, args.vm_name, f'{args.vm_name}.vhdx')

    print('Converting disk with virt-v2v (installs virtio drivers)...')
    convert_disk(vhdx_path, args.qcow_path)

    print('Creating VM on Proxmox...')
    proxmox.create_vm(args.proxmox_node, args.vmid, args.vm_name, args.cores, args.memory)

    print('Importing disk to Proxmox storage...')
    proxmox.import_disk(args.proxmox_node, args.vmid, args.qcow_path, args.storage)
    proxmox.set_virtio_disk(args.proxmox_node, args.vmid, args.storage)

    print('Starting VM on Proxmox...')
    proxmox.start_vm(args.proxmox_node, args.vmid)

    print('Migration complete.')


if __name__ == '__main__':
    main()
