#!/usr/bin/env python3
"""Refresh the profile's generated skill links from the public skills repository."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

OWNER = "cortezbuilds"
REPOSITORY = "happy-people-agent-skills"
BRANCH = "main"
BEGIN = "<!-- BEGIN HAPPY PEOPLE SKILLS -->"
END = "<!-- END HAPPY PEOPLE SKILLS -->"


def title(slug: str) -> str:
    acronyms = {"ai", "mcp", "oss"}
    return " ".join(word.upper() if word in acronyms else word.capitalize() for word in slug.split("-"))


def main() -> None:
    request = Request(
        f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/git/trees/{BRANCH}?recursive=1",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=30) as response:
        tree = json.load(response)["tree"]

    docs: dict[str, str] = {}
    for entry in tree:
        parts = entry["path"].split("/")
        if len(parts) != 3 or parts[0] != "skills" or parts[2] not in {"README.md", "SKILL.md"}:
            continue
        slug, filename = parts[1], parts[2]
        if filename == "README.md" or slug not in docs:
            docs[slug] = entry["path"]

    if not docs:
        raise RuntimeError("No per-skill README.md or SKILL.md files found")

    links = [
        f"- [{title(slug)}](https://github.com/{OWNER}/{REPOSITORY}/blob/{BRANCH}/{docs[slug]})"
        for slug in sorted(docs)
    ]
    readme_path = Path("README.md")
    readme = readme_path.read_text()
    before, separator, rest = readme.partition(BEGIN)
    if not separator:
        raise RuntimeError(f"Missing marker: {BEGIN}")
    _, separator, after = rest.partition(END)
    if not separator:
        raise RuntimeError(f"Missing marker: {END}")
    readme_path.write_text(f"{before}{BEGIN}\n" + "\n".join(links) + f"\n{END}{after}")


if __name__ == "__main__":
    main()
