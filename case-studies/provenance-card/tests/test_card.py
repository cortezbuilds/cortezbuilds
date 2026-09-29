"""Offline checks for the portable provenance case study (stdlib only)."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
import mobile_card  # noqa: E402
import provenance_card as card  # noqa: E402


class CardTests(unittest.TestCase):
    def test_saved_files_match_deterministic_rendering(self) -> None:
        manifest = card.load_json(PACKAGE / "manifest.json")
        card.validate_manifest(manifest)
        digest = card.manifest_digest(manifest)
        desktop = card.render_svg(manifest, digest)
        self.assertEqual((PACKAGE / "card.svg").read_bytes(), desktop)
        self.assertEqual(card.load_json(PACKAGE / "receipt.json"), card.make_receipt(manifest, desktop))

        phone = mobile_card.render_mobile(manifest, digest)
        self.assertEqual((PACKAGE / "card-mobile.svg").read_bytes(), phone)
        self.assertEqual(
            card.load_json(PACKAGE / "mobile-receipt.json"),
            mobile_card.expected_receipt(digest, phone, card.make_receipt(manifest, desktop)),
        )

    def test_phone_has_full_content_and_pinned_links(self) -> None:
        manifest = card.load_json(PACKAGE / "manifest.json")
        digest = card.manifest_digest(manifest)
        root = ET.fromstring((PACKAGE / "card-mobile.svg").read_bytes())
        self.assertEqual(root.attrib["viewBox"], "0 0 360 1630")
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        visible = " ".join(node.text or "" for node in root.findall(".//svg:text", namespace))
        for claim in manifest["claims"]:
            self.assertIn(claim["card_title"], visible)
            self.assertIn(claim["card_detail"], visible)
        for label, _ in card.CLASSES.values():
            self.assertIn(label, visible)
        self.assertIn(digest[:32], visible)
        self.assertIn(digest[32:], visible)

        links = [node.attrib["href"] for node in root.findall("svg:a", namespace)]
        self.assertEqual(len(links), 2)
        self.assertIn("654c51648f43bfa861c1f9bdc1fa3dbee2ec4c4d", links[0])
        self.assertIn("#L7-L14", links[0])
        self.assertIn("1f0c3e17d3e99a47241ebc00abdbe4e8071c7a5b", links[1])

    def test_private_decision_has_no_fake_public_permalink_or_local_dependency(self) -> None:
        manifest = card.load_json(PACKAGE / "manifest.json")
        decision = card.evidence_by_id(manifest, "E4")
        self.assertIsNone(decision["url"])
        self.assertFalse(decision["public_permalink"])
        self.assertFalse(decision["private_transcript_published"])
        self.assertFalse(any("local_path" in item for item in manifest["evidence"]))
        self.assertFalse(any("local_sha256" in item for item in manifest["evidence"]))

    def test_verification_works_after_copy_to_clean_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            for name in ("manifest.json", "receipt.json", "mobile-receipt.json",
                         "card.svg", "card-mobile.svg", "provenance_card.py", "mobile_card.py"):
                shutil.copy2(PACKAGE / name, target / name)
            for script in ("provenance_card.py", "mobile_card.py"):
                result = subprocess.run(
                    [sys.executable, script, "verify"], cwd=target,
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            # A changed output must not validate against the saved unsigned receipt.
            (target / "card-mobile.svg").write_bytes(
                (target / "card-mobile.svg").read_bytes().replace(b"REVIEW BRANCH", b"REVIEW CHANGE")
            )
            result = subprocess.run(
                [sys.executable, "mobile_card.py", "verify"], cwd=target,
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            json.loads('{"id":"E1","id":"E2"}', object_pairs_hook=card.no_duplicate_keys)


if __name__ == "__main__":
    unittest.main()
