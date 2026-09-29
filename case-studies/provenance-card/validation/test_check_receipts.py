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

    def mutate_spec_and_rehash(self, change) -> None:
        spec_path = self.validation / f"{NAME}.spec.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        change(spec)
        spec_path.write_text(json.dumps(spec), encoding="utf-8")

        def update_receipt(receipt: dict) -> None:
            receipt["spec"] = {"path": f"validation/{NAME}.spec.json",
                               **check_receipts.sha256_file(spec_path)}
            receipt["command"] = spec["command"]

        self.mutate(update_receipt)

    def test_saved_receipt_matches_reviewed_files(self) -> None:
        self.check()

    def test_duplicate_success_keys_are_rejected(self) -> None:
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        del receipt["success"]
        encoded = json.dumps(receipt)
        self.receipt_path.write_text(encoded[:-1] + ', "success": false, "success": true}',
                                     encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "duplicate receipt JSON key: success"):
            self.check()

    def test_rehashed_spec_with_invalid_schema_is_rejected(self) -> None:
        self.mutate_spec_and_rehash(lambda spec: spec.update(schema_version="build-trace-spec/999"))
        with self.assertRaisesRegex(ValueError, "invalid build trace spec schema"):
            self.check()

    def test_rehashed_spec_with_empty_command_is_rejected(self) -> None:
        self.mutate_spec_and_rehash(lambda spec: spec.update(command=[]))
        with self.assertRaisesRegex(ValueError, "command must be a nonempty list"):
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

    def test_group_quiescence_is_required(self) -> None:
        self.mutate(lambda receipt: receipt.update(group_quiescent=False))
        with self.assertRaisesRegex(ValueError, "trace incomplete or failed"):
            self.check()

    def test_background_descendant_is_rejected(self) -> None:
        self.mutate(lambda receipt: receipt.update(background_descendants_seen=True))
        with self.assertRaisesRegex(ValueError, "process group capture incomplete"):
            self.check()

    def test_malformed_stream_digest_is_rejected(self) -> None:
        self.mutate(lambda receipt: receipt["stdout"].update(sha256="not-a-digest"))
        with self.assertRaisesRegex(ValueError, "invalid stdout digest"):
            self.check()

    def test_negative_stream_byte_count_is_rejected(self) -> None:
        self.mutate(lambda receipt: receipt["stderr"].update(bytes=-1))
        with self.assertRaisesRegex(ValueError, "invalid stderr digest"):
            self.check()

    def test_matching_malformed_executable_digests_are_rejected(self) -> None:
        def corrupt(receipt: dict) -> None:
            for label in ("executable", "executable_after"):
                receipt[label] = {"sha256": "not-a-digest", "bytes": -1}

        self.mutate(corrupt)
        with self.assertRaisesRegex(ValueError, "invalid executable digest"):
            self.check()

    def test_invalid_utc_timestamps_are_rejected(self) -> None:
        self.mutate(lambda receipt: receipt.update(started_at_utc="not-a-time",
                                                   finished_at_utc="2026-09-29"))
        with self.assertRaisesRegex(ValueError, "invalid UTC timestamp"):
            self.check()

    def test_non_utc_timestamp_is_rejected(self) -> None:
        self.mutate(lambda receipt: receipt.update(started_at_utc="2026-09-29T13:20:00+01:00"))
        with self.assertRaisesRegex(ValueError, "invalid UTC timestamp"):
            self.check()

    def test_negative_or_reversed_monotonic_timing_is_rejected(self) -> None:
        self.mutate(lambda receipt: receipt.update(started_monotonic_ns=100,
                                                   finished_monotonic_ns=1,
                                                   duration_monotonic_ns=-99))
        with self.assertRaisesRegex(ValueError, "invalid monotonic timing"):
            self.check()

    def test_inconsistent_monotonic_duration_is_rejected(self) -> None:
        self.mutate(lambda receipt: receipt.update(duration_monotonic_ns=0))
        with self.assertRaisesRegex(ValueError, "invalid monotonic timing"):
            self.check()

    def test_overstated_capture_boundary_is_rejected(self) -> None:
        self.mutate(lambda receipt: receipt.update(capture_boundary="complete_host_and_model_capture"))
        with self.assertRaisesRegex(ValueError, "unexpected trace capture boundary/scope"):
            self.check()

    def test_overstated_scope_is_rejected(self) -> None:
        self.mutate(lambda receipt: receipt.update(scope="Every model and host action was captured."))
        with self.assertRaisesRegex(ValueError, "unexpected trace capture boundary/scope"):
            self.check()


if __name__ == "__main__":
    unittest.main()
