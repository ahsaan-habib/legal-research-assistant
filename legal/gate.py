"""Citation gate. In law an invented section number isn't an embarrassment,
it's the whole failure, so the answer is checked before it goes out:

  1. every claim sentence carries at least one [n]
  2. every [n] points at a provision we actually gave the model
  3. each claim is close in meaning to a sentence in the provision(s) it cites

Any failure -> refuse. No partial answers with the bad sentence removed: a
legal explanation with a hole cut out of it reads as complete.
"""
from __future__ import annotations

import re

import numpy as np

from .ingest import Provision
from .retrieve import embedder

_CITE = re.compile(r"\[(\d+)\]")
_SENT = re.compile(r"(?<=[.!?])\s+")
# sentences that relate facts to law but don't state law themselves
_FRAMING = re.compile(r"^(based on|from what you|you (said|mentioned|described)|if |whether |this depends)", re.I)


def claims(text: str) -> list[str]:
    out = []
    for para in text.split("\n"):
        for s in _SENT.split(para.strip(" -*")):
            if len(s.split()) >= 6 and not _FRAMING.match(s):
                out.append(s.strip())
    return out


def check(text: str, provs: list[Provision], threshold: float = 0.6) -> list[str]:
    problems = []
    cs = claims(text)
    for c in cs:
        nums = [int(n) for n in _CITE.findall(c)]
        if not nums:
            problems.append(f"uncited claim: {c[:80]}")
        elif any(not 1 <= n <= len(provs) for n in nums):
            problems.append(f"cites a provision that wasn't provided: {c[:80]}")
    if problems:
        return problems

    enc = embedder()
    for c in cs:
        nums = sorted({int(n) for n in _CITE.findall(c)})
        sents = [s for n in nums for s in _SENT.split(provs[n - 1].text) if len(s.split()) >= 4]
        if not sents:
            continue
        cv = enc.encode(_CITE.sub("", c), normalize_embeddings=True)
        sv = enc.encode(sents, normalize_embeddings=True)
        if float(np.max(sv @ cv)) < threshold:
            problems.append(f"claim not supported by what it cites: {c[:80]}")
    return problems
