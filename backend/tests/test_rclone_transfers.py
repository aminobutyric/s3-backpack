import subprocess
from collections.abc import Sequence

import pytest

from app.transfers import (
    RcloneTransferService,
    TransferExecutionError,
    TransferPlan,
    TransferStage,
)


class RecordingRunner:
    def __init__(self, returncodes: list[int] | None = None) -> None:
        self.commands: list[tuple[str, ...]] = []
        self.returncodes = returncodes or [0]

    def __call__(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        self.commands.append(tuple(command))
        returncode = self.returncodes.pop(0)
        return subprocess.CompletedProcess(
            args=list(command),
            returncode=returncode,
            stdout='{"msg":"ok"}\n' if returncode == 0 else "",
            stderr="" if returncode == 0 else "transfer failed",
        )


def test_backup_uses_non_destructive_copy_then_one_way_check() -> None:
    runner = RecordingRunner([0, 0])
    service = RcloneTransferService(
        config_path="/config/rclone/rclone.conf",
        command_runner=runner,
    )

    result = service.execute(
        TransferPlan(
            source="cloud:photos/2026",
            destination="backpack:photos/2026",
        )
    )

    assert result.verified
    assert runner.commands[0] == (
        "rclone",
        "--config",
        "/config/rclone/rclone.conf",
        "copy",
        "cloud:photos/2026",
        "backpack:photos/2026",
        "--metadata",
        "--check-first",
        "--use-json-log",
        "--stats=1s",
    )
    assert runner.commands[1][-2:] == ("--one-way", "--use-json-log")
    assert "sync" not in runner.commands[0]
    assert not any(argument.startswith("--delete") for argument in runner.commands[0])


def test_dry_run_does_not_run_verification() -> None:
    runner = RecordingRunner([0])
    service = RcloneTransferService(command_runner=runner)

    result = service.execute(
        TransferPlan("cloud:bucket", "backpack:bucket", dry_run=True)
    )

    assert "--dry-run" in runner.commands[0]
    assert len(runner.commands) == 1
    assert not result.verified


@pytest.mark.parametrize(
    "source,destination",
    [
        ("--config=/tmp/hostile", "backpack:bucket"),
        ("cloud:bucket\n--delete", "backpack:bucket"),
        ("cloud:bucket", "cloud:bucket"),
        ("not-a-remote", "backpack:bucket"),
    ],
)
def test_transfer_plan_rejects_unsafe_or_invalid_paths(
    source: str,
    destination: str,
) -> None:
    with pytest.raises(ValueError):
        TransferPlan(source, destination)


def test_failed_copy_stops_before_verification() -> None:
    runner = RecordingRunner([9])
    service = RcloneTransferService(command_runner=runner)

    with pytest.raises(TransferExecutionError) as exc:
        service.execute(TransferPlan("cloud:bucket", "backpack:bucket"))

    assert exc.value.stage is TransferStage.COPY
    assert exc.value.returncode == 9
    assert len(runner.commands) == 1


def test_failed_verification_is_not_reported_as_success() -> None:
    runner = RecordingRunner([0, 1])
    service = RcloneTransferService(command_runner=runner)

    with pytest.raises(TransferExecutionError) as exc:
        service.execute(TransferPlan("cloud:bucket", "backpack:bucket"))

    assert exc.value.stage is TransferStage.VERIFY
    assert exc.value.returncode == 1
