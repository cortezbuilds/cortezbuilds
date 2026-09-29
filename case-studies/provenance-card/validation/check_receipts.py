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
    if not item.get("exists"):
        raise ValueError(f"missing observed file: {item['path']}")
    path = (CARD / item["path"]).resolve()
    if not path.is_relative_to(CARD) or not path.is_file():
        raise ValueError(f"missing reviewed file: {item['path']}")
    if sha256_file(path) != {"sha256": item["sha256"], "bytes": item["bytes"]}:
        raise ValueError(f"reviewed file differs from trace: {item['path']}")


def check(name: str) -> None:
    spec_path = HERE / f"{name}.spec.json"
    receipt_path = HERE / "receipts" / f"{name}.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt["schema_version"] != "build-trace/1" or receipt["root"] != ".":
        raise ValueError(f"unexpected trace schema/root: {name}")
    if receipt["spec"] != {"path": f"validation/{name}.spec.json", **sha256_file(spec_path)}:
        raise ValueError(f"trace spec changed: {name}")
    if receipt["command"] != spec["command"]:
        raise ValueError(f"trace command changed: {name}")
    if not all(receipt[key] for key in ("capture_complete", "success", "input_stable", "executable_stable")):
        raise ValueError(f"trace incomplete or failed: {name}")
    if receipt["status"] != "completed" or receipt["exit_code"] != 0 or receipt["timed_out"]:
        raise ValueError(f"command did not complete successfully: {name}")
    if [item["path"] for item in receipt["inputs_before"]] != spec["inputs"]:
        raise ValueError(f"declared inputs differ: {name}")
    if [item["path"] for item in receipt["outputs_after"]] != spec["outputs"]:
        raise ValueError(f"declared outputs differ: {name}")
    for item in (*receipt["inputs_before"], *receipt["outputs_after"]):
        check_file(item)
    if name in BUILD_STEPS and any(item["exists"] for item in receipt["outputs_before"]):
        raise ValueError(f"build outputs existed before run: {name}")


if __name__ == "__main__":
    try:
        for name in NAMES:
            check(name)
    except (OSError, KeyError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS: {len(NAMES)} captured subprocess steps match reviewed files (unsigned local consistency)")
