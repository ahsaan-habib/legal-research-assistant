"""Fetch a UK Public General Act from legislation.gov.uk (Open Government
Licence) and write it in this project's corpus format, one `##` per section.

    python scripts/fetch_ukpga.py 2015 15 "Consumer Rights Act 2015"

Uses the CLML XML (`.../data.xml`). The as-enacted vs latest-revised question
matters for law: this takes the latest revised version the site serves, and
records the fetch date in the file so it's visible how current it is.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import httpx

NS = {"l": "http://www.legislation.gov.uk/namespaces/legislation"}


def text_of(el) -> str:
    return " ".join(" ".join(el.itertext()).split())


def main(year: str, number: str, title: str, jurisdiction: str = "UK") -> None:
    url = f"https://www.legislation.gov.uk/ukpga/{year}/{number}/data.xml"
    xml = httpx.get(url, timeout=60, follow_redirects=True).text
    root = ET.fromstring(xml)
    sections = []
    for group in root.iter(f"{{{NS['l']}}}P1group"):
        heading = group.find("l:Title", NS)
        for p1 in group.findall("l:P1", NS):
            num = p1.find("l:Pnumber", NS)
            body = text_of(p1)
            if num is not None and body:
                body = body[len(text_of(num)):].strip() if body.startswith(text_of(num)) else body
                sections.append((text_of(num), text_of(heading) if heading is not None else "", body))

    out = Path("corpus/uk") / f"ukpga-{year}-{number}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", f"jurisdiction: {jurisdiction}", f"instrument: {title}", f"source: {url}",
             f"fetched: {date.today().isoformat()}", "---"]
    for num, heading, body in sections:
        lines += [f"## Section {num} — {heading}", body, ""]
    out.write_text("\n".join(lines))
    print(f"{len(sections)} sections -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
