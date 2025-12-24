"""Issue-spot, retrieve jurisdiction-filtered law, answer only with citations,
refuse otherwise."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import llm, retrieve
from .ingest import Provision
from .issues import spot

CANNOT = "CANNOT_GROUND"

SYSTEM = f"""You explain what the provided legal provisions say about the user's
situation. You are not a lawyer and you do not give advice on what to do.

Rules:
- Use ONLY the numbered provisions. Every sentence that states what the law
  says ends with the provision number(s), like [2].
- Quote time limits, amounts and conditions exactly as written.
- Do not mention any statute, case, section, time limit or right that is not
  in the provisions.
- Explain how the provisions relate to the facts, and say plainly which facts
  would change the answer.
- If the provisions don't address the question, reply exactly {CANNOT}."""


@dataclass
class Consultation:
    status: str                              # answered | need_jurisdiction | refused
    text: str = ""
    citations: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    jurisdiction: str | None = None
    urgent: bool = False
    options: list[str] = field(default_factory=list)


def consult(description: str, jurisdiction: str | None = None) -> Consultation:
    known = retrieve.jurisdictions()
    s = spot(description, known)
    jur = (jurisdiction or s.jurisdiction or "").upper() or None
    if jur not in known:
        return Consultation("need_jurisdiction", issues=s.issues, urgent=s.urgent, options=known)

    provisions: dict[str, Provision] = {}
    for q in s.issues:
        for p, _ in retrieve.search(q, jur):
            provisions.setdefault(p.id, p)
    provs = list(provisions.values())[:8]
    if not provs:
        return Consultation("refused", issues=s.issues, jurisdiction=jur, urgent=s.urgent)

    context = "\n\n".join(f"[{i}] {p.citation} — {p.section}\n{p.text}" for i, p in enumerate(provs, 1))
    facts = "\n".join(f"- {f}" for f in s.facts) or description
    text = llm.chat([{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": f"Provisions:\n{context}\n\nFacts:\n{facts}\n\nQuestions: {'; '.join(s.issues)}"}])
    if CANNOT in text:
        return Consultation("refused", issues=s.issues, jurisdiction=jur, urgent=s.urgent)
    cited = [p.citation for i, p in enumerate(provs, 1) if f"[{i}]" in text]
    return Consultation("answered", text.strip(), cited, s.issues, jur, s.urgent)
