"""Mutation checks for the unsigned build-receipt consistency checker."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

import check_receipts


SOURCE_CARD = Path(__file__).resolve().parents[1]
NAME = "desktop-build"


class CheckReceiptsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.card = Path(self.temp.name)
        self.validation = self.card / "validation"
        self.receipt_path = self.validation / "receipts" / f"{NAME}.json"
        self.receipt_path.parent.mkdir(parents=True)

        spec_source = SOURCE_CARD / "validation" / f"{NAME}.spec.json"
        shutil.copy2(spec_source, self.validation / spec_source.name)
        spec = json.loads(spec_source.read_text(encoding="utf-8"))
        for relative in [*spec["inputs"], *spec["outputs"]]:
            destination = self.card / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE_CARD / relative, destination)
        shutil.copy2(SOURCE_CARD / "validation" / "receipts" / f"{NAME}.json",
                     self.receipt_path)

    def check(self) -> None:
        with (mock.patch.object(check_receipts, "CARD", self.card),
              mock.patch.object(check_receipts, "HERE", self.validation)):
            check_receipts.check(NAME)

    def mutate(self, change) -> None:
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        change(receipt)
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    def test_saved_receipt_matches_reviewed_files(self) -> None:
        self.check()

    def test_changed_input_after_snapshot_fails(self) -> None:
        self.mutate(lambda receipt: receipt["inputs_after"][0].update(sha256="0" * 64))
        with self.assertRaisesRegex(ValueError, "reviewed file differs from trace"):
            self.check()

    def test_missing_input_after_row_fails(self) -> None:
        self.mutate(lambda receipt: receipt["inputs_after"].pop())
        with self.assertRaisesRegex(ValueError, "declared inputs_after differ"):
            self.check()

    def test_reordered_output_before_rows_fail(self) -> None:
        self.mutate(lambda receipt: receipt["outputs_before"].reverse())
        with self.assertRaisesRegex(ValueError, "declared outputs_before differ"):
            self.check()

    def test_preexisting_build_output_claim_fails(self) -> None:
        def claim_preexisting(receipt: dict) -> None:
            output = receipt["outputs_after"][0]
            receipt["outputs_before"][0] = output.copy()

        self.mutate(claim_preexisting)
        with self.assertRaisesRegex(ValueError, "unexpected outputs_before existence"):
            self.check()

    def test_input_stability_flag_must_agree_with_snapshots(self) -> None:
        self.mutate(lambda receipt: receipt.update(input_stable=False))
        with self.assertRaisesRegex(ValueError, "trace incomplete or failed"):
            self.check()

    def test_stream_completion_flag_is_checked(self) -> None:
        self.mutate(lambda receipt: receipt["stdout"].update(complete=False))
        with self.assertRaisesRegex(ValueError, "incomplete captured stdout"):
            self.check()


if __name__ == "__main__":
    unittest.main()
