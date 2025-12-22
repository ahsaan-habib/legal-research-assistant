"""Issue spotting: turn a story into searchable legal questions.

The model also says which jurisdiction the user is in — but only if the user
said so. A guessed jurisdiction is worse than asking, because everything
downstream is filtered by it.
"""
from __future__ import annotations

import json

from pydantic import BaseModel, Field, ValidationError

from . import llm


class Spotted(BaseModel):
    jurisdiction: str | None = Field(None, description="code from the allowed list, or null if not stated")
    issues: list[str] = Field(description="each a short search query in legal terms")
    facts: list[str] = Field(description="the key facts, in the user's own terms")
    urgent: bool = Field(description="deadlines, court papers, eviction, arrest, imminent harm")


SYSTEM = """You help organise a legal question. Do not answer it.

From the user's description extract:
- jurisdiction: one of {codes}, ONLY if the user stated where they are or the
  place is unambiguous. Otherwise null. Never guess.
- issues: 1-4 short queries naming the legal questions (e.g. "refund for faulty
  goods after 30 days", "landlord withholding deposit").
- facts: the key facts that matter to those questions.
- urgent: true if there is a deadline, court or tribunal papers, eviction,
  arrest, or risk of harm.
Reply as JSON."""


def spot(description: str, jurisdictions: list[str]) -> Spotted:
    raw = llm.chat([{"role": "system", "content": SYSTEM.format(codes=", ".join(jurisdictions))},
                    {"role": "user", "content": description}], fmt=Spotted.model_json_schema())
    try:
        s = Spotted.model_validate_json(raw)
    except (ValidationError, json.JSONDecodeError):
        return Spotted(jurisdiction=None, issues=[description[:200]], facts=[], urgent=False)
    if s.jurisdiction and s.jurisdiction.upper() not in jurisdictions:
        s.jurisdiction = None       # not one we hold law for: ask, don't map
    return s
