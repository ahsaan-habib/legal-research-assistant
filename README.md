# legal-research-assistant

Blueprint 3 from *Designing AI Automation for Your Business*: someone
describes their situation, and the system explains what the law it holds for
their jurisdiction says — with a citation on every statement — or refuses.

> General legal information, not legal advice. The bundled `corpus/examplia/`
> is a **fictional** jurisdiction for trying the pipeline; it is not the law
> anywhere. Ingest real legislation before using it for anything.

```
description ─▶ issue spotting (queries, facts, urgency; jurisdiction only if stated)
            ─▶ no jurisdiction? ask — never guess
            ─▶ retrieval with jurisdiction as a hard where-filter (no unfiltered path)
            ─▶ explanation from the provisions only, [n] after every legal statement
            ─▶ citation gate: uncited claim / citation to nothing / claim that doesn't
               match what it cites  ──▶ refuse
            ─▶ framing in code: urgent banner, lawyer brief, disclaimer — always
```

## Why it's built this way

- **Jurisdiction is a filter, not a hint.** The law in one place isn't the
  law in another. `retrieve.search` requires a jurisdiction and passes it as a
  Chroma `where` clause; there's no function that searches everything.
- **Refuse rather than guess.** An invented section number or time limit is
  malpractice-shaped, not an embarrassment. A gated answer either survives all
  three checks or becomes a refusal — never a partial answer with the bad
  sentence cut out, which would read as complete.
- **The framing can't be prompted away.** Disclaimer, urgency banner and the
  "what to bring to a lawyer" brief are attached by `present.py`, not asked
  of the model.
- **Positioned as triage.** The output is meant to get someone to a lawyer
  better prepared: their facts, the questions to ask, the provisions that may
  apply.

## Run it

```bash
ollama pull qwen3:4b
python -m venv .venv && .venv/bin/pip install -e . && source .venv/bin/activate
legal index
legal ask "I bought a kettle online 3 weeks ago in Examplia and it stopped working" -j EX
uvicorn legal.api:app --port 8040
```

Real UK legislation (Open Government Licence):

```bash
python scripts/fetch_ukpga.py 2015 15 "Consumer Rights Act 2015"
legal index
```

Fetched files record their source URL and fetch date. Legislation changes;
re-fetch before relying on it.
