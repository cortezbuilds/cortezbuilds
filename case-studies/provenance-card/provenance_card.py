#!/usr/bin/env python3
"""Build or verify a portable, deterministic provenance card. No network calls."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import sys
import unicodedata


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"
CARD = HERE / "card.svg"
RECEIPT = HERE / "receipt.json"
DOMAIN = b"provenance-card/1\0"
CLASSES = {
    "source": ("SOURCE", "#68A8FF"),
    "observed": ("OBSERVED", "#4DD4A4"),
    "decision": ("DECISION", "#C29BFF"),
    "inference": ("INFERENCE", "#F0BC6B"),
    "unknown": ("UNKNOWN", "#A8B4C5"),
}


def no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_float(value: str) -> None:
    raise ValueError(f"floating-point JSON value is outside this canonical subset: {value}")


def load_json(path: Path) -> dict:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=no_duplicate_keys,
        parse_float=reject_float,
        parse_constant=reject_float,
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def check_canonical_subset(value: object) -> None:
    """Use only normalized strings, ASCII keys, integers, booleans, null and arrays."""
    if isinstance(value, dict):
        for key, child in value.items():
            if not key.isascii():
                raise ValueError(f"non-ASCII manifest key: {key}")
            check_canonical_subset(child)
    elif isinstance(value, list):
        for child in value:
            check_canonical_subset(child)
    elif isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise ValueError("non-NFC manifest string")
    elif value is None or isinstance(value, (bool, int)):
        return
    else:
        raise ValueError(f"unsupported manifest value: {type(value).__name__}")


def canonical_manifest_bytes(manifest: dict) -> bytes:
    check_canonical_subset(manifest)
    return json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_digest(manifest: dict) -> str:
    return sha256(DOMAIN + canonical_manifest_bytes(manifest))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def evidence_by_id(manifest: dict, evidence_id: str) -> dict:
    return next(item for item in manifest["evidence"] if item["id"] == evidence_id)


def claim_by_id(manifest: dict, claim_id: str) -> dict:
    return next(item for item in manifest["claims"] if item["id"] == claim_id)


def render_svg(manifest: dict, digest: str) -> bytes:
    claims = [claim_by_id(manifest, f"C{n}") for n in range(1, 6)]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="920" viewBox="0 0 1280 920" role="img" aria-labelledby="title desc">',
        '<title id="title">A reversible mistake — provenance card</title>',
        '<desc id="desc">The published README change, its revert, a private decision to draft for review, a proposed control, and unverified deployment states. Color classes also have text labels.</desc>',
        '<defs>',
        '<linearGradient id="back" x2="1" y2="1"><stop stop-color="#07111E"/><stop offset="1" stop-color="#11283A"/></linearGradient>',
        '<radialGradient id="glow"><stop stop-color="#1B5E79" stop-opacity=".43"/><stop offset="1" stop-color="#1B5E79" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="accent" x2="1" y2="0"><stop stop-color="#5FE2C0"/><stop offset="1" stop-color="#68A8FF"/></linearGradient>',
        '</defs>',
        '<rect width="1280" height="920" fill="url(#back)"/>',
        '<circle cx="1070" cy="150" r="410" fill="url(#glow)"/>',
        '<path d="M0 208H1280" stroke="#244155" stroke-width="1"/>',
        '<rect x="62" y="41" width="7" height="25" rx="3.5" fill="url(#accent)"/>',
        '<text x="84" y="60" fill="#9FC6D6" font-family="DejaVu Sans, Arial, sans-serif" font-size="15" font-weight="700" letter-spacing="2">PROVENANCE STUDY / 001</text>',
        '<text x="62" y="135" fill="#F2F8FB" font-family="DejaVu Sans, Arial, sans-serif" font-size="54" font-weight="700">A reversible mistake</text>',
        '<text x="64" y="177" fill="#B6CBD5" font-family="DejaVu Sans, Arial, sans-serif" font-size="18">A public README edit, its restoration, and a beliefs draft prepared for review.</text>',
        '<rect x="62" y="230" width="718" height="324" rx="20" fill="#112335" stroke="#2A4558"/>',
        '<text x="90" y="264" fill="#9FC6D6" font-family="DejaVu Sans, Arial, sans-serif" font-size="14" font-weight="700" letter-spacing="1.4">THE TRACE</text>',
        '<path d="M107 318V483" stroke="#35536A" stroke-width="3" stroke-linecap="round"/>',
        '<rect x="806" y="230" width="412" height="324" rx="20" fill="#112335" stroke="#2A4558"/>',
        '<text x="834" y="264" fill="#9FC6D6" font-family="DejaVu Sans, Arial, sans-serif" font-size="14" font-weight="700" letter-spacing="1.4">EXACT RECORD ID</text>',
    ]

    row_y = [286, 374, 462]
    for claim, y in zip(claims[:3], row_y):
        label, color = CLASSES[claim["class"]]
        url = evidence_by_id(manifest, claim["evidence_ids"][0]).get("url")
        if url:
            out.append(f'<a href="{esc(url)}">')
        out.extend(
            [
                f'<rect x="88" y="{y}" width="664" height="72" rx="13" fill="#182E42" stroke="#325169"/>',
                f'<circle cx="107" cy="{y + 36}" r="8" fill="{color}"/>',
                f'<text x="129" y="{y + 28}" fill="#F2F8FB" font-family="DejaVu Sans, Arial, sans-serif" font-size="17" font-weight="700">{esc(claim["card_title"])}</text>',
                f'<text x="129" y="{y + 53}" fill="#AAC4D0" font-family="DejaVu Sans, Arial, sans-serif" font-size="13">{esc(claim["card_detail"])}</text>',
                f'<text x="731" y="{y + 29}" text-anchor="end" fill="{color}" font-family="DejaVu Sans, Arial, sans-serif" font-size="12" font-weight="700">{label}</text>',
            ]
        )
        if url:
            out.append('</a>')

    # A branching constellation. The solid route depicts the observed sequence;
    # its dashed continuation is a proposed review path, not a historical Git
    # branch. Dim stars are placed deterministically from digest bytes.
    digest_bytes = bytes.fromhex(digest)
    for index, byte in enumerate(digest_bytes[:26]):
        x = 841 + ((index * 131 + byte) % 357)
        y = 284 + ((index * 47 + byte * 3) % 151)
        radius = 1 + (byte % 3)
        out.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="#91CEDD" opacity=".18"/>')
    out.extend(
        [
            '<path d="M849 383 C883 383 885 328 925 328 S967 383 997 383 S1060 383 1092 383" fill="none" stroke="#36556C" stroke-width="15" stroke-linecap="round" opacity=".25"/>',
            '<path d="M849 383 C883 383 885 328 925 328 S967 383 997 383 S1060 383 1092 383" fill="none" stroke="url(#accent)" stroke-width="3" stroke-linecap="round"/>',
            '<path d="M1092 383 C1136 383 1136 321 1182 321" fill="none" stroke="#F0BC6B" stroke-width="3" stroke-linecap="round" stroke-dasharray="6 7"/>',
            '<path d="M1092 383 C1136 383 1136 416 1182 416" fill="none" stroke="#A8B4C5" stroke-width="2" stroke-linecap="round" stroke-dasharray="3 7" opacity=".7"/>',
            '<circle cx="849" cy="383" r="8" fill="#68A8FF" stroke="#D9F4FF" stroke-width="2"/>',
            '<circle cx="925" cy="328" r="10" fill="#68A8FF" stroke="#D9F4FF" stroke-width="2"/>',
            '<circle cx="997" cy="383" r="10" fill="#4DD4A4" stroke="#D9F4FF" stroke-width="2"/>',
            '<circle cx="1092" cy="383" r="10" fill="#C29BFF" stroke="#EADFFF" stroke-width="2"/>',
            '<circle cx="1182" cy="321" r="9" fill="#152A3B" stroke="#F0BC6B" stroke-width="2"/>',
            '<circle cx="1182" cy="416" r="9" fill="#152A3B" stroke="#A8B4C5" stroke-width="2"/>',
            '<text x="925" y="306" text-anchor="middle" fill="#A9CEFB" font-family="DejaVu Sans, Arial, sans-serif" font-size="11" font-weight="700">EDIT</text>',
            '<text x="997" y="414" text-anchor="middle" fill="#8AE5C4" font-family="DejaVu Sans, Arial, sans-serif" font-size="11" font-weight="700">RESTORE</text>',
            '<text x="1092" y="414" text-anchor="middle" fill="#D7BFFF" font-family="DejaVu Sans, Arial, sans-serif" font-size="11" font-weight="700">DRAFT</text>',
            '<text x="1182" y="300" text-anchor="middle" fill="#F0BC6B" font-family="DejaVu Sans, Arial, sans-serif" font-size="11" font-weight="700">PROPOSED</text>',
            '<text x="1182" y="440" text-anchor="middle" fill="#A8B4C5" font-family="DejaVu Sans, Arial, sans-serif" font-size="11" font-weight="700">UNKNOWN</text>',
            '<path d="M834 455H1190" stroke="#29475A"/>',
            '<text x="834" y="476" fill="#8FABBA" font-family="DejaVu Sans, Arial, sans-serif" font-size="11" letter-spacing="1.1">MANIFEST SHA-256 · EXACT RECORD ID</text>',
            f'<text x="834" y="499" fill="#D7F8ED" font-family="DejaVu Sans Mono, monospace" font-size="13">{digest[:32]}</text>',
            f'<text x="834" y="520" fill="#D7F8ED" font-family="DejaVu Sans Mono, monospace" font-size="13">{digest[32:]}</text>',
            '<text x="834" y="540" fill="#91ABB7" font-family="DejaVu Sans, Arial, sans-serif" font-size="11">Solid: recorded sequence. Dashed: proposals and unknowns.</text>',
        ]
    )

    for claim, x in zip(claims[3:], [62, 652]):
        label, color = CLASSES[claim["class"]]
        out.extend(
            [
                f'<rect x="{x}" y="578" width="566" height="100" rx="17" fill="#152A3B" stroke="#2A4558"/>',
                f'<rect x="{x}" y="578" width="5" height="100" rx="2" fill="{color}"/>',
                f'<text x="{x + 23}" y="610" fill="{color}" font-family="DejaVu Sans, Arial, sans-serif" font-size="12" font-weight="700" letter-spacing="1.2">{label}</text>',
                f'<text x="{x + 23}" y="638" fill="#F2F8FB" font-family="DejaVu Sans, Arial, sans-serif" font-size="19" font-weight="700">{esc(claim["card_title"])}</text>',
                f'<text x="{x + 23}" y="660" fill="#A8C2CE" font-family="DejaVu Sans, Arial, sans-serif" font-size="13">{esc(claim["card_detail"])}</text>',
            ]
        )

    out.append('<text x="62" y="727" fill="#9FC6D6" font-family="DejaVu Sans, Arial, sans-serif" font-size="13" font-weight="700" letter-spacing="1.3">PROVENANCE CLASSES</text>')
    for index, (kind, (label, color)) in enumerate(CLASSES.items()):
        x = 62 + index * 225
        out.extend(
            [
                f'<circle cx="{x + 8}" cy="751" r="6" fill="{color}"/>',
                f'<text x="{x + 23}" y="756" fill="#C8D9E2" font-family="DejaVu Sans, Arial, sans-serif" font-size="13" font-weight="700">{label}</text>',
            ]
        )

    stage_titles = ["LOCAL CASE STUDY", "REVIEW BRANCH", "PROFILE MAIN", "RELEASE"]
    for index, (stage, title) in enumerate(zip(manifest["stage_states"], stage_titles)):
        x = 62 + index * 292
        status = "GENERATED" if stage["state"] == "generated" else "UNVERIFIED"
        color = "#4DD4A4" if stage["state"] == "generated" else "#A8B4C5"
        out.extend(
            [
                f'<rect x="{x}" y="787" width="274" height="76" rx="13" fill="#0C1D2C" stroke="#294255"/>',
                f'<text x="{x + 16}" y="815" fill="#A7BFCA" font-family="DejaVu Sans, Arial, sans-serif" font-size="12" font-weight="700">{title}</text>',
                f'<text x="{x + 16}" y="843" fill="{color}" font-family="DejaVu Sans, Arial, sans-serif" font-size="16" font-weight="700">{status}</text>',
            ]
        )
    out.extend(
        [
            '<text x="62" y="901" fill="#91ABB7" font-family="DejaVu Sans, Arial, sans-serif" font-size="12">Snapshot 2026-09-29 · Source links are commit pinned · Decision context is private and unlinked</text>',
            '</svg>',
        ]
    )
    return ('\n'.join(out) + '\n').encode('utf-8')


def validate_manifest(manifest: dict) -> None:
    if manifest.get("schema_version") != "provenance-card/1":
        raise ValueError("unsupported manifest schema_version")
    evidence = manifest["evidence"]
    claims = manifest["claims"]
    if len({item["id"] for item in evidence}) != len(evidence):
        raise ValueError("duplicate evidence ID")
    if len({item["id"] for item in claims}) != len(claims):
        raise ValueError("duplicate claim ID")
    known = {item["id"] for item in evidence}
    for item in evidence + claims:
        if item["class"] not in CLASSES:
            raise ValueError(f"unknown provenance class: {item['class']}")
    for claim in claims:
        if not set(claim["evidence_ids"]) <= known:
            raise ValueError(f"claim {claim['id']} refers to missing evidence")
    if manifest["media_inputs"]["actual_image"] or manifest["media_inputs"]["actual_audio"]:
        raise ValueError("this prototype has no image or audio source inputs")
    if any("local_path" in item for item in evidence):
        raise ValueError("portable case study must not depend on local file paths")


def make_receipt(manifest: dict, svg: bytes) -> dict:
    return {
        "schema_version": "provenance-card-receipt/1",
        "canonicalization": "UTF-8 JSON; ASCII keys sorted; compact separators; NFC strings; no floats; prefixed with provenance-card/1 NUL",
        "manifest_sha256": manifest_digest(manifest),
        "card_svg_sha256": sha256(svg),
        "signature": None,
        "scope": "File consistency only; this unsigned receipt does not prove authorship, complete event capture, skill execution, publication, or release."
    }


def build() -> None:
    manifest = load_json(MANIFEST)
    validate_manifest(manifest)
    digest = manifest_digest(manifest)
    svg = render_svg(manifest, digest)
    CARD.write_bytes(svg)
    receipt = make_receipt(manifest, svg)
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built card.svg and receipt.json; manifest SHA-256 {digest}")


def verify() -> None:
    manifest = load_json(MANIFEST)
    validate_manifest(manifest)
    expected_svg = render_svg(manifest, manifest_digest(manifest))
    actual_svg = CARD.read_bytes()
    if actual_svg != expected_svg:
        raise ValueError("card.svg does not match the deterministic rendering of manifest.json")
    expected_receipt = make_receipt(manifest, actual_svg)
    if load_json(RECEIPT) != expected_receipt:
        raise ValueError("receipt.json does not match the manifest and card")
    print(f"PASS: manifest {expected_receipt['manifest_sha256']}")
    print(f"PASS: card SVG {expected_receipt['card_svg_sha256']}")
    print("This offline check does not re-query remote links or prove the private decision context.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "verify"])
    args = parser.parse_args()
    try:
        if args.action == "build":
            build()
        else:
            verify()
    except (ValueError, KeyError, FileNotFoundError, TypeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
