from typing import Any

import pytest
from fastapi import HTTPException

from app.api.disks import list_disks
from app.disks import (
    DiskDiscoveryError,
    DiskInfo,
    LsblkDiskDiscovery,
    parse_lsblk_inventory,
)


def _device(**overrides: Any) -> dict[str, Any]:
    device: dict[str, Any] = {
        "name": "sda",
        "kname": "sda",
        "path": "/dev/sda",
        "type": "disk",
        "size": 1_000_000,
        "fstype": None,
        "fsver": None,
        "label": None,
        "uuid": None,
        "mountpoints": [None],
        "rm": False,
        "ro": False,
        "tran": "sata",
        "model": "Example Disk",
        "serial": "SERIAL-1",
        "pkname": None,
    }
    device.update(overrides)
    return device


def test_inventory_marks_candidate_and_propagates_system_disk_risk() -> None:
    data_disk = _device(
        children=[
            _device(
                name="sda1",
                kname="sda1",
                path="/dev/sda1",
                type="part",
                size=900_000,
                fstype="xfs",
                uuid="data-uuid",
                mountpoints=["/mnt/backpack"],
                tran=None,
                model=None,
                serial=None,
                pkname="sda",
            )
        ]
    )
    system_disk = _device(
        name="nvme0n1",
        kname="nvme0n1",
        path="/dev/nvme0n1",
        tran="nvme",
        model="System SSD",
        serial="SYSTEM-1",
        children=[
            _device(
                name="nvme0n1p1",
                kname="nvme0n1p1",
                path="/dev/nvme0n1p1",
                type="part",
                fstype="ext4",
                uuid="root-uuid",
                mountpoints=["/"],
                tran=None,
                model=None,
                serial=None,
                pkname="nvme0n1",
            ),
            _device(
                name="nvme0n1p2",
                kname="nvme0n1p2",
                path="/dev/nvme0n1p2",
                type="part",
                fstype="ext4",
                uuid="other-uuid",
                mountpoints=["/mnt/other"],
                tran=None,
                model=None,
                serial=None,
                pkname="nvme0n1",
            ),
        ],
    )

    inventory = parse_lsblk_inventory(
        {"blockdevices": [data_disk, system_disk]}
    )
    by_path = {disk.path: disk for disk in inventory}

    candidate = by_path["/dev/sda1"]
    assert candidate.ready
    assert not candidate.system_disk
    assert candidate.root_device_path == "/dev/sda"
    assert candidate.transport == "sata"
    assert candidate.model == "Example Disk"
    assert candidate.serial == "SERIAL-1"

    assert by_path["/dev/nvme0n1"].system_disk
    assert by_path["/dev/nvme0n1p1"].system_disk
    assert by_path["/dev/nvme0n1p2"].system_disk
    assert "system_disk" in by_path["/dev/nvme0n1p2"].blocking_reasons
    assert not by_path["/dev/nvme0n1p2"].ready


def test_inventory_reports_unmounted_unsupported_and_read_only_reasons() -> None:
    inventory = parse_lsblk_inventory(
        {
            "blockdevices": [
                _device(
                    fstype="vfat",
                    uuid="usb-uuid",
                    mountpoints=[],
                    rm=True,
                    ro=True,
                    tran="usb",
                )
            ]
        }
    )

    disk = inventory[0]
    assert disk.removable
    assert disk.transport == "usb"
    assert not disk.ready
    assert disk.blocking_reasons == (
        "read_only",
        "unsupported_filesystem",
        "not_mounted",
    )


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"blockdevices": "invalid"},
        {"blockdevices": [{}]},
        {"blockdevices": [_device(size=-1)]},
    ],
)
def test_inventory_rejects_malformed_lsblk_output(payload: object) -> None:
    with pytest.raises(DiskDiscoveryError):
        parse_lsblk_inventory(payload)


class StubDiscovery(LsblkDiskDiscovery):
    def __init__(
        self,
        disks: list[DiskInfo] | None = None,
        error: DiskDiscoveryError | None = None,
    ) -> None:
        self.disks = disks or []
        self.error = error

    def discover(self) -> list[DiskInfo]:
        if self.error:
            raise self.error
        return self.disks


def test_disk_api_returns_classified_inventory() -> None:
    disk = parse_lsblk_inventory(
        {
            "blockdevices": [
                _device(
                    fstype="xfs",
                    uuid="data-uuid",
                    mountpoints=["/mnt/backpack"],
                )
            ]
        }
    )[0]

    response = list_disks(StubDiscovery([disk]))

    assert response.disks[0].uuid == "data-uuid"
    assert response.disks[0].ready
    assert response.disks[0].blocking_reasons == []


def test_disk_api_returns_503_when_inventory_is_unavailable() -> None:
    with pytest.raises(HTTPException) as exc:
        list_disks(StubDiscovery(error=DiskDiscoveryError("not available")))

    assert exc.value.status_code == 503
    assert exc.value.detail == "Block-device inventory is unavailable."
