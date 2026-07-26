from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import Any

from app.config import get_settings

LSBLK_COLUMNS = (
    "NAME,KNAME,PATH,TYPE,SIZE,FSTYPE,FSVER,LABEL,UUID,MOUNTPOINTS,"
    "RM,RO,TRAN,MODEL,SERIAL,PKNAME"
)
SUPPORTED_FILESYSTEMS = frozenset({"btrfs", "ext4", "xfs"})
SYSTEM_MOUNTPOINTS = frozenset({"/", "/boot", "/boot/efi", "/home", "/usr", "/var"})
INVENTORIED_DEVICE_TYPES = frozenset({"disk", "part"})


class DiskDiscoveryError(RuntimeError):
    pass


@dataclass(frozen=True)
class DiskInfo:
    name: str
    path: str
    device_type: str
    parent_path: str | None
    root_device_path: str
    size: int
    filesystem: str | None
    filesystem_version: str | None
    label: str | None
    uuid: str | None
    mountpoints: tuple[str, ...]
    removable: bool
    read_only: bool
    transport: str | None
    model: str | None
    serial: str | None
    system_disk: bool = False
    ready: bool = False
    blocking_reasons: tuple[str, ...] = ()


class LsblkDiskDiscovery:
    """Read block-device metadata without mounting or opening a device."""

    def __init__(self, binary: str = "lsblk") -> None:
        self.binary = binary

    def discover(self) -> list[DiskInfo]:
        command = [
            self.binary,
            "--json",
            "--bytes",
            "--output",
            LSBLK_COLUMNS,
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                check=False,
                text=True,
            )
        except FileNotFoundError as exc:
            raise DiskDiscoveryError(
                f"Block-device inventory executable not found: {self.binary}"
            ) from exc
        except OSError as exc:
            raise DiskDiscoveryError(str(exc)) from exc

        if completed.returncode != 0:
            detail = completed.stderr.strip() or "lsblk returned no error detail"
            raise DiskDiscoveryError(detail)

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise DiskDiscoveryError("lsblk returned invalid JSON") from exc
        return parse_lsblk_inventory(payload)


def parse_lsblk_inventory(payload: object) -> list[DiskInfo]:
    if not isinstance(payload, Mapping):
        raise DiskDiscoveryError("lsblk output must be a JSON object")
    raw_devices = payload.get("blockdevices")
    if not isinstance(raw_devices, list):
        raise DiskDiscoveryError("lsblk output is missing blockdevices")

    devices: list[DiskInfo] = []
    for raw_device in raw_devices:
        if not isinstance(raw_device, Mapping):
            raise DiskDiscoveryError("lsblk returned an invalid block device")
        devices.extend(_parse_device_tree(raw_device))

    system_roots = {
        device.root_device_path
        for device in devices
        if SYSTEM_MOUNTPOINTS.intersection(device.mountpoints)
    }
    return [_classify_device(device, system_roots) for device in devices]


def _parse_device_tree(
    raw: Mapping[str, Any],
    parent_path: str | None = None,
    root: DiskInfo | None = None,
) -> list[DiskInfo]:
    device_type = _required_string(raw, "type")
    path = _required_string(raw, "path")
    current = DiskInfo(
        name=_required_string(raw, "name"),
        path=path,
        device_type=device_type,
        parent_path=parent_path,
        root_device_path=root.root_device_path if root else path,
        size=_non_negative_int(raw.get("size"), "size"),
        filesystem=_optional_string(raw.get("fstype")),
        filesystem_version=_optional_string(raw.get("fsver")),
        label=_optional_string(raw.get("label")),
        uuid=_optional_string(raw.get("uuid")),
        mountpoints=_mountpoints(raw.get("mountpoints")),
        removable=_boolean(raw.get("rm")),
        read_only=_boolean(raw.get("ro")),
        transport=_optional_string(raw.get("tran")),
        model=_optional_string(raw.get("model")),
        serial=_optional_string(raw.get("serial")),
    )
    physical_root = root or current
    inherited = replace(
        current,
        removable=current.removable or physical_root.removable,
        transport=current.transport or physical_root.transport,
        model=current.model or physical_root.model,
        serial=current.serial or physical_root.serial,
    )

    parsed = [inherited] if device_type in INVENTORIED_DEVICE_TYPES else []
    children = raw.get("children", [])
    if children is None:
        children = []
    if not isinstance(children, list):
        raise DiskDiscoveryError(f"Invalid children for block device {path}")
    for child in children:
        if not isinstance(child, Mapping):
            raise DiskDiscoveryError(f"Invalid child for block device {path}")
        parsed.extend(_parse_device_tree(child, path, physical_root))
    return parsed


def _classify_device(device: DiskInfo, system_roots: set[str]) -> DiskInfo:
    reasons: list[str] = []
    system_disk = device.root_device_path in system_roots
    if system_disk:
        reasons.append("system_disk")
    if device.read_only:
        reasons.append("read_only")
    if device.filesystem is None:
        reasons.append("no_filesystem")
    elif device.filesystem.lower() not in SUPPORTED_FILESYSTEMS:
        reasons.append("unsupported_filesystem")
    if device.uuid is None:
        reasons.append("missing_uuid")
    if not device.mountpoints:
        reasons.append("not_mounted")
    return replace(
        device,
        system_disk=system_disk,
        ready=not reasons,
        blocking_reasons=tuple(reasons),
    )


def _required_string(raw: Mapping[str, Any], key: str) -> str:
    value = _optional_string(raw.get(key))
    if value is None:
        raise DiskDiscoveryError(f"lsblk device is missing {key}")
    return value


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DiskDiscoveryError("lsblk returned a non-string field")
    normalized = value.strip()
    return normalized or None


def _non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DiskDiscoveryError(f"lsblk returned an invalid {field_name}")
    return value


def _boolean(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    raise DiskDiscoveryError("lsblk returned an invalid boolean field")


def _mountpoints(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    values: Sequence[object]
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        raise DiskDiscoveryError("lsblk returned invalid mountpoints")

    mountpoints: list[str] = []
    for item in values:
        mountpoint = _optional_string(item)
        if mountpoint is not None and mountpoint not in mountpoints:
            mountpoints.append(mountpoint)
    return tuple(mountpoints)


@lru_cache
def get_disk_discovery() -> LsblkDiskDiscovery:
    return LsblkDiskDiscovery(get_settings().lsblk_binary)
