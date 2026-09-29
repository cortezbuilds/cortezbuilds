#!/usr/bin/env python3
"""Check saved build traces against the reviewed case-study files."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import json
import re
import sys

from trace_build import sha256_file


CARD = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
NAMES = ("desktop-build", "mobile-build", "desktop-verify", "mobile-verify", "tests", "png-render")
BUILD_STEPS = {"desktop-build", "mobile-build", "png-render"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$")
CAPTURE_BOUNDARY = "controlled_subprocess_stdio_and_declared_files"
CAPTURE_SCOPE = (
    "Linux same-process-group metadata only: declared-file hashes and captured stdio digests. "
    "New-session/group descendants, model context, host activity, and all-process I/O "
    "are outside this capture."
)


def check_digest(item: object, label: str, keys: set[str]) -> None:
    if not isinstance(item, dict) or set(item) != keys:
        raise ValueError(f"invalid {label} fields")
    if (not isinstance(item["sha256"], str) or not SHA256.fullmatch(item["sha256"]) or
            type(item["bytes"]) is not int or item["bytes"] < 0):
        raise ValueError(f"invalid {label} digest or byte count")


def check_timing(receipt: dict) -> None:
    for label in ("started_at_utc", "finished_at_utc"):
        value = receipt[label]
        if not isinstance(value, str) or not UTC_TIMESTAMP.fullmatch(value):
            raise ValueError(f"invalid UTC timestamp: {label}")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(f"invalid UTC timestamp: {label}") from error
        if parsed.utcoffset() != timedelta(0):
            raise ValueError(f"invalid UTC timestamp: {label}")
    fields = ("started_monotonic_ns", "finished_monotonic_ns", "duration_monotonic_ns")
    if any(type(receipt[label]) is not int or receipt[label] < 0 for label in fields):
        raise ValueError("invalid monotonic timing")
    if (receipt["finished_monotonic_ns"] < receipt["started_monotonic_ns"] or
            receipt["duration_monotonic_ns"] !=
            receipt["finished_monotonic_ns"] - receipt["started_monotonic_ns"]):
        raise ValueError("invalid monotonic timing")


def check_file(item: dict) -> None:
    path = (CARD / item["path"]).resolve()
    if not path.is_relative_to(CARD) or not path.is_file():
        raise ValueError(f"missing reviewed file: {item['path']}")
    if sha256_file(path) != {"sha256": item["sha256"], "bytes": item["bytes"]}:
        raise ValueError(f"reviewed file differs from trace: {item['path']}")


def check_snapshot(items: list[dict], paths: list[str], label: str, *,
                   present: bool | None = None, compare_current: bool = False) -> None:
    if (not isinstance(items, list) or any(not isinstance(item, dict) for item in items) or
            [item.get("path") for item in items] != paths):
        raise ValueError(f"declared {label} differ")
    for item in items:
        exists = item.get("exists")
        if type(exists) is not bool or (present is not None and exists is not present):
            raise ValueError(f"unexpected {label} existence: {item['path']}")
        expected_keys = {"path", "exists", "sha256", "bytes"} if exists else {"path", "exists"}
        if set(item) != expected_keys:
            raise ValueError(f"invalid {label} snapshot: {item['path']}")
        if compare_current:
            check_file(item)


def check(name: str) -> None:
    spec_path = HERE / f"{name}.spec.json"
    receipt_path = HERE / "receipts" / f"{name}.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt["schema_version"] != "build-trace/1" or receipt["root"] != "." or receipt["cwd"] != ".":
        raise ValueError(f"unexpected trace schema/root: {name}")
    if (receipt["capture_boundary"] != CAPTURE_BOUNDARY or
            receipt["scope"] != CAPTURE_SCOPE):
        raise ValueError(f"unexpected trace capture boundary/scope: {name}")
    if receipt["spec"] != {"path": f"validation/{name}.spec.json", **sha256_file(spec_path)}:
        raise ValueError(f"trace spec changed: {name}")
    if receipt["command"] != spec["command"] or receipt["timeout_seconds"] != spec["timeout_seconds"]:
        raise ValueError(f"trace command changed: {name}")
    check_timing(receipt)
    if any(receipt[key] is not True for key in (
        "capture_complete", "success", "input_stable", "executable_stable", "group_quiescent"
    )):
        raise ValueError(f"trace incomplete or failed: {name}")
    if (receipt["group_observation"] != "linux_procfs_waitid_wnowait" or
            receipt["background_descendants_seen"] is not False):
        raise ValueError(f"process group capture incomplete: {name}")
    if (receipt["status"] != "completed" or type(receipt["exit_code"]) is not int or
            receipt["exit_code"] != 0 or receipt["timed_out"] is not False or receipt["error"] is not None):
        raise ValueError(f"command did not complete successfully: {name}")
    for stream in ("stdout", "stderr"):
        state = receipt[stream]
        check_digest(state, stream, {"sha256", "bytes", "complete", "error"})
        if state["complete"] is not True or state["error"] is not None:
            raise ValueError(f"incomplete captured {stream}: {name}")
    for label in ("executable", "executable_after"):
        check_digest(receipt[label], label, {"sha256", "bytes"})
    if receipt["executable"] != receipt["executable_after"]:
        raise ValueError(f"executable changed during capture: {name}")
    check_snapshot(receipt["inputs_before"], spec["inputs"], "inputs_before", present=True,
                   compare_current=True)
    check_snapshot(receipt["inputs_after"], spec["inputs"], "inputs_after", present=True,
                   compare_current=True)
    check_snapshot(receipt["outputs_before"], spec["outputs"], "outputs_before",
                   present=False if name in BUILD_STEPS else None)
    check_snapshot(receipt["outputs_after"], spec["outputs"], "outputs_after", present=True,
                   compare_current=True)
    if receipt["inputs_before"] != receipt["inputs_after"]:
        raise ValueError(f"declared inputs changed during capture: {name}")
    if receipt["declared_outputs_present"] is not True:
        raise ValueError(f"declared outputs missing after capture: {name}")


if __name__ == "__main__":
    try:
        for name in NAMES:
            check(name)
    except (OSError, KeyError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS: {len(NAMES)} captured subprocess steps match reviewed files (unsigned local consistency)")
