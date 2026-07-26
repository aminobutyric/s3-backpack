from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum

RCLONE_REMOTE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*:[^\x00\r\n]*$")

CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


class TransferStage(StrEnum):
    COPY = "copy"
    VERIFY = "verify"


@dataclass(frozen=True)
class TransferPlan:
    """A one-way cloud-to-local transfer using named rclone remotes."""

    source: str
    destination: str
    verify: bool = True
    dry_run: bool = False

    def __post_init__(self) -> None:
        _validate_remote_path(self.source, "source")
        _validate_remote_path(self.destination, "destination")
        if self.source == self.destination:
            raise ValueError("Source and destination must be different.")


@dataclass(frozen=True)
class TransferCommandResult:
    stage: TransferStage
    command: tuple[str, ...]
    stdout: str
    stderr: str


@dataclass(frozen=True)
class TransferRunResult:
    copy: TransferCommandResult
    verification: TransferCommandResult | None

    @property
    def verified(self) -> bool:
        return self.verification is not None


class TransferExecutionError(RuntimeError):
    def __init__(
        self,
        stage: TransferStage,
        returncode: int | None,
        detail: str,
    ) -> None:
        self.stage = stage
        self.returncode = returncode
        self.detail = detail
        code = "unavailable" if returncode is None else str(returncode)
        super().__init__(f"Rclone {stage.value} failed ({code}): {detail}")


class RcloneTransferService:
    """Build and execute a constrained subset of rclone operations."""

    def __init__(
        self,
        binary: str = "rclone",
        config_path: str | None = None,
        command_runner: CommandRunner | None = None,
    ) -> None:
        if not binary or "\x00" in binary or "\n" in binary or "\r" in binary:
            raise ValueError("Rclone binary must be a valid executable path.")
        self.binary = binary
        self.config_path = config_path
        self._command_runner = command_runner or _run_command

    def build_copy_command(self, plan: TransferPlan) -> list[str]:
        command = [
            *self._base_command(),
            "copy",
            plan.source,
            plan.destination,
            "--metadata",
            "--check-first",
            "--use-json-log",
            "--stats=1s",
        ]
        if plan.dry_run:
            command.append("--dry-run")
        return command

    def build_check_command(self, plan: TransferPlan) -> list[str]:
        return [
            *self._base_command(),
            "check",
            plan.source,
            plan.destination,
            "--one-way",
            "--use-json-log",
        ]

    def execute(self, plan: TransferPlan) -> TransferRunResult:
        copy_result = self._execute_stage(
            TransferStage.COPY,
            self.build_copy_command(plan),
        )
        verification = None
        if plan.verify and not plan.dry_run:
            verification = self._execute_stage(
                TransferStage.VERIFY,
                self.build_check_command(plan),
            )
        return TransferRunResult(copy=copy_result, verification=verification)

    def _base_command(self) -> list[str]:
        command = [self.binary]
        if self.config_path:
            command.extend(["--config", self.config_path])
        return command

    def _execute_stage(
        self,
        stage: TransferStage,
        command: Sequence[str],
    ) -> TransferCommandResult:
        try:
            completed = self._command_runner(command)
        except FileNotFoundError as exc:
            raise TransferExecutionError(
                stage,
                None,
                f"executable not found: {self.binary}",
            ) from exc
        except OSError as exc:
            raise TransferExecutionError(stage, None, str(exc)) from exc

        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise TransferExecutionError(
                stage,
                completed.returncode,
                detail or "no error detail was returned",
            )

        return TransferCommandResult(
            stage=stage,
            command=tuple(command),
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


def _validate_remote_path(value: str, field_name: str) -> None:
    if not RCLONE_REMOTE_PATTERN.fullmatch(value):
        raise ValueError(
            f"{field_name.capitalize()} must be a named rclone remote path."
        )


def _run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        capture_output=True,
        check=False,
        text=True,
    )
