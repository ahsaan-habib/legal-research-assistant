"""What the user actually sees. The framing is attached in code, not left to
the model, so it can't be talked out of the prompt."""
from __future__ import annotations

from .consult import Consultation

DISCLAIMER = ("This is general legal information, not legal advice. It may not cover every rule "
              "that applies to you or reflect recent changes. Talk to a qualified lawyer before acting on it.")
URGENT = ("This sounds time-sensitive. If there is a deadline, court or tribunal papers, or a risk to "
          "your safety or housing, contact a lawyer or advice service now rather than waiting.")
REFUSED = ("I couldn't find provisions in the law I have for {jur} that clearly answer this, so I won't "
           "guess. A lawyer can look at the full picture.")


def lawyer_brief(c: Consultation, facts: list[str] | None = None) -> str:
    """What to bring to a lawyer: the person arrives better prepared either way."""
    lines = ["What to bring to a lawyer:"]
    if facts:
        lines += ["  Key facts:"] + [f"   - {f}" for f in facts]
    if c.issues:
        lines += ["  Questions to ask:"] + [f"   - {q}" for q in c.issues]
    if c.citations:
        lines += ["  Provisions that may be relevant:"] + [f"   - {x}" for x in c.citations]
    lines.append("  Any contracts, receipts, letters, emails and dates you have.")
    return "\n".join(lines)


def render(c: Consultation, facts: list[str] | None = None) -> str:
    parts = []
    if c.urgent:
        parts.append(URGENT)
    if c.status == "need_jurisdiction":
        parts.append("Which jurisdiction are you in? I only search law for the place you're in. "
                     f"Available: {', '.join(c.options)}.")
    elif c.status == "refused":
        parts.append(REFUSED.format(jur=c.jurisdiction))
    else:
        parts.append(c.text)
        parts.append("Sources: " + "; ".join(c.citations))
    if c.status != "need_jurisdiction":
        parts.append(lawyer_brief(c, facts))
    parts.append(DISCLAIMER)
    return "\n\n".join(parts)
