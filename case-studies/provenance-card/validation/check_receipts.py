#!/usr/bin/env python3
"""Check saved build traces against the reviewed case-study files."""

from __future__ import annotations

from pathlib import Path
import json
import sys

from trace_build import sha256_file


CARD = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
NAMES = ("desktop-build", "mobile-build", "desktop-verify", "mobile-verify", "tests", "png-render")
BUILD_STEPS = {"desktop-build", "mobile-build", "png-render"}


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
    if receipt["spec"] != {"path": f"validation/{name}.spec.json", **sha256_file(spec_path)}:
        raise ValueError(f"trace spec changed: {name}")
    if receipt["command"] != spec["command"] or receipt["timeout_seconds"] != spec["timeout_seconds"]:
        raise ValueError(f"trace command changed: {name}")
    if any(receipt[key] is not True for key in ("capture_complete", "success", "input_stable", "executable_stable")):
        raise ValueError(f"trace incomplete or failed: {name}")
    if (receipt["status"] != "completed" or type(receipt["exit_code"]) is not int or
            receipt["exit_code"] != 0 or receipt["timed_out"] is not False or receipt["error"] is not None):
        raise ValueError(f"command did not complete successfully: {name}")
    for stream in ("stdout", "stderr"):
        if receipt[stream]["complete"] is not True or receipt[stream]["error"] is not None:
            raise ValueError(f"incomplete captured {stream}: {name}")
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
