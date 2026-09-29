#!/usr/bin/env python3
"""Build or verify a phone-width view of the portable provenance card.

The original manifest, desktop SVG, and receipt are read-only inputs. This
variant has its own SVG and receipt because its bytes differ from the desktop
card even though the underlying record ID is identical.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import provenance_card as source


HERE = Path(__file__).resolve().parent
MOBILE_CARD = HERE / "card-mobile.svg"
MOBILE_RECEIPT = HERE / "mobile-receipt.json"
WIDTH = 360
HEIGHT = 1630
FONT = "DejaVu Sans, Arial, sans-serif"
MONO = "DejaVu Sans Mono, monospace"


def text(x: int, y: int, value: object, size: int, color: str,
         *, weight: int | None = None, anchor: str | None = None,
         spacing: str | None = None, family: str = FONT) -> str:
    attrs = [f'x="{x}"', f'y="{y}"', f'fill="{color}"',
             f'font-family="{family}"', f'font-size="{size}"']
    if weight is not None:
        attrs.append(f'font-weight="{weight}"')
    if anchor is not None:
        attrs.append(f'text-anchor="{anchor}"')
    if spacing is not None:
        attrs.append(f'letter-spacing="{spacing}"')
    return f'<text {" ".join(attrs)}>{source.esc(value)}</text>'


def render_mobile(manifest: dict, digest: str) -> bytes:
    """Render a 360 px wide view; no CSS scaling or viewport clipping."""
    source.validate_manifest(manifest)
    if manifest["title"] != "A reversible mistake":
        raise ValueError("this layout is for the dated 'A reversible mistake' snapshot")
    claims = [source.claim_by_id(manifest, f"C{number}") for number in range(1, 6)]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="mobile-title mobile-desc">',
        '<title id="mobile-title">A reversible mistake — mobile provenance card</title>',
        '<desc id="mobile-desc">A phone-width view of the provenance record. The README addition and revert link to commit-pinned GitHub records. The private decision to draft for review, proposal, and unverified deployment states are labeled separately. The full manifest SHA-256 appears below.</desc>',
        '<defs>',
        '<linearGradient id="mobile-back" x2="1" y2="1"><stop stop-color="#07111E"/><stop offset="1" stop-color="#11283A"/></linearGradient>',
        '<radialGradient id="mobile-glow"><stop stop-color="#1B5E79" stop-opacity=".42"/><stop offset="1" stop-color="#1B5E79" stop-opacity="0"/></radialGradient>',
        '<linearGradient id="mobile-accent" x2="1" y2="0"><stop stop-color="#5FE2C0"/><stop offset="1" stop-color="#68A8FF"/></linearGradient>',
        '</defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#mobile-back)"/>',
        '<circle cx="340" cy="120" r="230" fill="url(#mobile-glow)"/>',
        '<rect x="20" y="25" width="6" height="23" rx="3" fill="url(#mobile-accent)"/>',
        text(38, 42, "PROVENANCE STUDY / 001", 13, "#9FC6D6", weight=700, spacing="1.2"),
        text(20, 91, "A reversible", 33, "#F2F8FB", weight=700),
        text(20, 129, "mistake", 33, "#F2F8FB", weight=700),
        text(21, 163, "A public README edit, its restoration,", 13, "#B6CBD5"),
        text(21, 185, "and a beliefs draft prepared", 13, "#B6CBD5"),
        text(21, 207, "for review.", 13, "#B6CBD5"),
        '<path d="M0 232H360" stroke="#244155"/>',
        '<rect x="16" y="252" width="328" height="355" rx="19" fill="#112335" stroke="#2A4558"/>',
        text(34, 284, "THE TRACE", 13, "#9FC6D6", weight=700, spacing="1.2"),
        '<path d="M47 329V531" stroke="#35536A" stroke-width="3" stroke-linecap="round"/>',
    ]

    for claim, y in zip(claims[:3], (303, 400, 497)):
        label, color = source.CLASSES[claim["class"]]
        url = source.evidence_by_id(manifest, claim["evidence_ids"][0]).get("url")
        if url:
            out.append(f'<a href="{source.esc(url)}">')
        out.extend([
            f'<rect x="30" y="{y}" width="300" height="88" rx="13" fill="#182E42" stroke="#325169"/>',
            f'<circle cx="47" cy="{y + 25}" r="7" fill="{color}"/>',
            text(65, y + 30, claim["card_title"], 15, "#F2F8FB", weight=700),
            text(65, y + 53, claim["card_detail"], 13, "#AAC4D0"),
            text(65, y + 75, label, 13, color, weight=700, spacing=".5"),
        ])
        if url:
            out.append('</a>')

    out.extend([
        '<rect x="16" y="625" width="328" height="284" rx="19" fill="#112335" stroke="#2A4558"/>',
    ])
    # The small star field is seeded by exact manifest digest bytes. It is a
    # visual fingerprint, while the printed digest remains the inspectable ID.
    for index, byte in enumerate(bytes.fromhex(digest)[:26]):
        x = 37 + ((index * 79 + byte) % 285)
        y = 669 + ((index * 31 + byte * 3) % 72)
        radius = 1 + byte % 3
        out.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="#91CEDD" opacity=".18"/>')
    out.extend([
        text(34, 657, "EXACT RECORD ID", 13, "#9FC6D6", weight=700, spacing="1.1"),
        '<path d="M63 707H224" fill="none" stroke="#36556C" stroke-width="13" stroke-linecap="round" opacity=".30"/>',
        '<path d="M63 707H224" fill="none" stroke="url(#mobile-accent)" stroke-width="3" stroke-linecap="round"/>',
        '<path d="M224 707C256 707 263 684 291 684" fill="none" stroke="#F0BC6B" stroke-width="2.5" stroke-dasharray="5 6"/>',
        '<path d="M224 707C256 707 263 734 291 734" fill="none" stroke="#A8B4C5" stroke-width="2.5" stroke-dasharray="4 6"/>',
        '<circle cx="63" cy="707" r="8" fill="#68A8FF" stroke="#D9F4FF" stroke-width="2"/>',
        '<circle cx="144" cy="707" r="8" fill="#4DD4A4" stroke="#D9F4FF" stroke-width="2"/>',
        '<circle cx="224" cy="707" r="8" fill="#C29BFF" stroke="#EADFFF" stroke-width="2"/>',
        '<circle cx="291" cy="684" r="8" fill="#152A3B" stroke="#F0BC6B" stroke-width="2"/>',
        '<circle cx="291" cy="734" r="8" fill="#152A3B" stroke="#A8B4C5" stroke-width="2"/>',
        text(63, 742, "EDIT", 13, "#A9CEFB", weight=700, anchor="middle"),
        text(144, 742, "RESTORE", 13, "#8AE5C4", weight=700, anchor="middle"),
        text(224, 742, "DRAFT", 13, "#D7BFFF", weight=700, anchor="middle"),
        '<path d="M34 758H326" stroke="#29475A"/>',
        text(34, 784, "MANIFEST SHA-256", 13, "#8FABBA", weight=700, spacing=".8"),
        text(34, 817, digest[:32], 13, "#D7F8ED", family=MONO),
        text(34, 842, digest[32:], 13, "#D7F8ED", family=MONO),
        text(34, 879, "Solid: recorded · dashed: possible paths", 13, "#91ABB7"),
    ])

    for claim, y in zip(claims[3:], (928, 1048)):
        label, color = source.CLASSES[claim["class"]]
        out.extend([
            f'<rect x="16" y="{y}" width="328" height="104" rx="17" fill="#152A3B" stroke="#2A4558"/>',
            f'<rect x="16" y="{y}" width="5" height="104" rx="2" fill="{color}"/>',
            text(39, y + 27, label, 13, color, weight=700, spacing=".7"),
            text(39, y + 59, claim["card_title"], 18, "#F2F8FB", weight=700),
            text(39, y + 84, claim["card_detail"], 13, "#A8C2CE"),
        ])

    out.append(text(20, 1187, "PROVENANCE CLASSES", 13, "#9FC6D6", weight=700, spacing="1"))
    class_places = ((39, 1219), (190, 1219), (39, 1250), (190, 1250), (39, 1281))
    for (label, color), (x, y) in zip(source.CLASSES.values(), class_places):
        out.append(f'<circle cx="{x - 13}" cy="{y - 5}" r="6" fill="{color}"/>')
        out.append(text(x, y, label, 13, "#C8D9E2", weight=700))

    out.append(text(20, 1326, "DEPLOYMENT STATE", 13, "#9FC6D6", weight=700, spacing="1"))
    stage_titles = ("LOCAL CASE STUDY", "REVIEW BRANCH", "PROFILE MAIN", "RELEASE")
    for index, (stage, title) in enumerate(zip(manifest["stage_states"], stage_titles)):
        if stage["state"] not in {"generated", "unverified"}:
            raise ValueError(f"unhandled stage state: {stage['state']}")
        x = 16 if index % 2 == 0 else 184
        y = 1343 if index < 2 else 1443
        status = "GENERATED" if stage["state"] == "generated" else "UNVERIFIED"
        color = "#4DD4A4" if stage["state"] == "generated" else "#A8B4C5"
        out.extend([
            f'<rect x="{x}" y="{y}" width="160" height="84" rx="13" fill="#0C1D2C" stroke="#294255"/>',
            text(x + 13, y + 28, title, 13, "#A7BFCA", weight=700),
            text(x + 13, y + 61, status, 15, color, weight=700),
        ])

    out.extend([
        text(20, 1570, "Snapshot 2026-09-29 · local case study", 13, "#91ABB7"),
        text(20, 1592, "Public source pinned · private decision unlinked", 13, "#91ABB7"),
        '</svg>',
    ])
    return ('\n'.join(out) + '\n').encode('utf-8')


def original_snapshot() -> tuple[dict, str, dict]:
    manifest = source.load_json(source.MANIFEST)
    source.validate_manifest(manifest)
    digest = source.manifest_digest(manifest)
    original_receipt = source.load_json(source.RECEIPT)
    if original_receipt["manifest_sha256"] != digest:
        raise ValueError("original manifest no longer matches the dated receipt")
    desktop_svg = source.CARD.read_bytes()
    if desktop_svg != source.render_svg(manifest, digest):
        raise ValueError("desktop SVG differs from deterministic rendering")
    if original_receipt != source.make_receipt(manifest, desktop_svg):
        raise ValueError("desktop receipt differs from the manifest and rendering")
    return manifest, digest, original_receipt


def expected_receipt(digest: str, svg: bytes, original_receipt: dict) -> dict:
    return {
        "schema_version": "provenance-card-mobile-receipt/1",
        "variant": "mobile-360",
        "manifest_sha256": digest,
        "desktop_card_svg_sha256": original_receipt["card_svg_sha256"],
        "mobile_card_svg_sha256": source.sha256(svg),
        "signature": None,
        "scope": "Derived view of the dated snapshot. Unsigned hashes show file consistency, not authorship, skill execution, publication, or release.",
    }


def build() -> None:
    manifest, digest, original_receipt = original_snapshot()
    svg = render_mobile(manifest, digest)
    receipt = expected_receipt(digest, svg, original_receipt)
    MOBILE_CARD.write_bytes(svg)
    MOBILE_RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    verify()


def verify() -> None:
    manifest, digest, original_receipt = original_snapshot()
    actual_svg = MOBILE_CARD.read_bytes()
    expected_svg = render_mobile(manifest, digest)
    if actual_svg != expected_svg:
        raise ValueError("mobile SVG differs from deterministic render")
    actual_receipt = source.load_json(MOBILE_RECEIPT)
    if actual_receipt != expected_receipt(digest, actual_svg, original_receipt):
        raise ValueError("mobile receipt differs from derived snapshot hashes")

    root = ET.fromstring(actual_svg)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    if root.attrib.get("viewBox") != f"0 0 {WIDTH} {HEIGHT}":
        raise ValueError("mobile SVG has unexpected viewport")
    visible = ' '.join((item.text or '') for item in root.findall('.//svg:text', namespace))
    for label, _ in source.CLASSES.values():
        if label not in visible:
            raise ValueError(f"missing visible class label: {label}")
    for claim in manifest["claims"]:
        if claim["card_title"] not in visible or claim["card_detail"] not in visible:
            raise ValueError(f"missing visible claim: {claim['id']}")
    if digest[:32] not in visible or digest[32:] not in visible:
        raise ValueError("full record ID is not visible")
    expected_links = [source.evidence_by_id(manifest, claim["evidence_ids"][0])["url"]
                      for claim in manifest["claims"][:2]]
    actual_links = [item.attrib["href"] for item in root.findall('svg:a', namespace)]
    if actual_links != expected_links:
        raise ValueError("mobile source links do not match manifest")
    print(f"OK: mobile {WIDTH}×{HEIGHT} SVG matches dated manifest {digest}; local integrity only")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify"))
    args = parser.parse_args()
    if args.command == "build":
        build()
    else:
        verify()


if __name__ == "__main__":
    main()
