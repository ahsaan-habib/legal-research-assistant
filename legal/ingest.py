"""Ingest legislation as one chunk per section, with the metadata that makes
retrieval jurisdiction-safe: jurisdiction, instrument, section, citation.

Corpus files are Markdown with front matter:

    ---
    jurisdiction: EX
    instrument: Examplia Consumer Sales Act 2019
    ---
    ## Section 7 — Short-term right to reject
    ...
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Provision:
    id: str
    jurisdiction: str
    instrument: str
    section: str
    text: str

    @property
    def citation(self) -> str:
        # the number must start with a digit, or "Schedule 2" reads as "s.chedule"
        num = re.match(r"(?:Section|s\.?)\s*(\d[\w.]*)", self.section, re.I)
        return f"{self.instrument}, s.{num.group(1)}" if num else f"{self.instrument}, {self.section}"


def parse_file(path: Path) -> list[Provision]:
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
    if not m:
        return []
    meta = yaml.safe_load(m.group(1))
    out = []
    for i, part in enumerate(re.split(r"^## ", raw[m.end():], flags=re.M)[1:]):
        heading, _, body = part.partition("\n")
        out.append(Provision(id=f"{path.stem}-{i}", jurisdiction=str(meta["jurisdiction"]).upper(),
                             instrument=meta["instrument"], section=heading.strip(), text=body.strip()))
    return out


def load_corpus(root: str = "corpus") -> list[Provision]:
    out: list[Provision] = []
    for path in sorted(Path(root).rglob("*.md")):
        if path.name.lower() != "readme.md":
            out.extend(parse_file(path))
    return out
