import functools
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from legal import api, consult as consult_mod, gate, retrieve
from legal.consult import consult
from legal.ingest import Provision, parse_file
from legal.issues import spot
from legal.present import DISCLAIMER, render

ROOT = Path(__file__).resolve().parents[1]
FAKE_MIN = 0.2      # min_score is tuned for bge-small; the fake embedder scores lower


def test_parse_file_and_citation():
    provs = parse_file(ROOT / "corpus/examplia/residential-tenancy-act.md")
    assert [p.section for p in provs][0] == "Section 5 — Deposits" and provs[0].jurisdiction == "EX"
    assert provs[0].citation == "Examplia Residential Tenancy Act 2016, s.5"
    assert Provision("x", "EX", "Act", "Schedule 2", "t").citation == "Act, Schedule 2"
    assert parse_file(ROOT / "corpus/examplia/README.md") == []


def test_retrieval_never_crosses_jurisdictions(indexed):
    assert indexed == 9 and retrieve.jurisdictions() == ["EX", "ZZ"]
    ex = retrieve.search("landlord deposit rent", "ex", min_score=FAKE_MIN)
    zz = retrieve.search("landlord deposit rent", "ZZ", min_score=FAKE_MIN)
    assert ex and all(p.jurisdiction == "EX" for p, _ in ex)
    assert [p.instrument for p, _ in zz] == ["Otherland Housing Act 2001"]
    try:
        retrieve.search("x", "")
        raise AssertionError("searched without a jurisdiction")
    except ValueError:
        pass


PROVS = [Provision("p1", "EX", "Examplia Residential Tenancy Act 2016", "Section 6 — Return of deposit",
                   "At the end of a tenancy the landlord must return the deposit within 21 days, less any "
                   "deductions for unpaid rent or damage beyond fair wear and tear.")]


def test_gate_checks_cites_range_and_support(indexed):
    ok = "The landlord must return the deposit within 21 days at the end of a tenancy [1]."
    assert gate.check(ok, PROVS) == []
    assert gate.check("If you moved out, this depends on the dates.", PROVS) == []      # framing, not law
    assert gate.check("The landlord must return the deposit within 21 days of the end.", PROVS)[0].startswith(
        "uncited claim")
    assert gate.check("The landlord must return the deposit within 21 days [2].", PROVS)[0].startswith(
        "cites a provision that wasn't provided")
    assert gate.check("Tenants can also claim triple damages from the housing tribunal [1].", PROVS)[0].startswith(
        "claim not supported")


def spotted(jur=None, issues=("landlord withholding deposit",), urgent=False):
    return json.dumps({"jurisdiction": jur, "issues": list(issues), "facts": ["moved out 5 weeks ago"],
                       "urgent": urgent})


def test_spot_never_keeps_a_jurisdiction_we_dont_hold(llm):
    llm(spotted("UK"))
    assert spot("I'm in the UK", ["EX"]).jurisdiction is None
    llm("broken")
    s = spot("my landlord kept my deposit", ["EX"])
    assert s.issues == ["my landlord kept my deposit"] and s.jurisdiction is None


def test_consult_asks_refuses_answers(indexed, llm, monkeypatch):
    monkeypatch.setattr(retrieve, "search", functools.partial(retrieve.search, min_score=FAKE_MIN))
    llm(spotted(None, urgent=True))
    c = consult("my landlord kept my deposit")
    assert c.status == "need_jurisdiction" and c.options == ["EX", "ZZ"] and c.urgent
    out = render(c)
    assert "Which jurisdiction" in out and out.endswith(DISCLAIMER) and "time-sensitive" in out

    llm(spotted("ex"), "CANNOT_GROUND")
    assert consult("deposit question").status == "refused"

    fake = llm(spotted("ex"), "Your landlord has to give it back eventually.")
    c = consult("deposit question")
    assert c.status == "refused" and c.problems and "uncited claim" in c.problems[0]
    assert "Otherland" not in fake.calls[1]["messages"][1]["content"]     # jurisdiction filter held

    good = "At the end of a tenancy the landlord must return the deposit within 21 days [{n}]."

    def answer_citing_the_deposit_section(messages, fmt=None):
        if fmt is not None:
            return spotted("ex")
        n = next(line.split("]")[0][1:] for line in messages[1]["content"].splitlines() if "Return of deposit" in line)
        return good.format(n=n)

    monkeypatch.setattr("legal.llm.chat", answer_citing_the_deposit_section)
    c = consult("deposit question", jurisdiction="EX")
    assert c.status == "answered" and c.citations == ["Examplia Residential Tenancy Act 2016, s.6"]
    out = render(c)
    assert "Sources: Examplia Residential Tenancy Act 2016, s.6" in out and "What to bring to a lawyer" in out


def test_api(indexed, llm):
    c = TestClient(api.app)
    assert c.get("/jurisdictions").json() == ["EX", "ZZ"]
    llm(spotted(None))
    r = c.post("/consult", json={"description": "deposit"}).json()
    assert r["status"] == "need_jurisdiction" and r["detail"]["options"] == ["EX", "ZZ"]


def test_fetch_ukpga_writes_corpus_format(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts"))
    import fetch_ukpga

    xml = ('<Legislation xmlns="http://www.legislation.gov.uk/namespaces/legislation"><Body>'
           '<P1group><Title>Goods to be of satisfactory quality</Title><P1><Pnumber>9</Pnumber>'
           '<P1para><Text>Every contract to supply goods is to be treated as including a term.</Text></P1para>'
           '</P1></P1group></Body></Legislation>')
    monkeypatch.setattr(fetch_ukpga.httpx, "get", lambda *a, **k: type("R", (), {"text": xml})())
    monkeypatch.chdir(tmp_path)
    fetch_ukpga.main("2015", "15", "Consumer Rights Act 2015")
    provs = parse_file(tmp_path / "corpus/uk/ukpga-2015-15.md")
    assert provs[0].citation == "Consumer Rights Act 2015, s.9" and provs[0].jurisdiction == "UK"
    assert provs[0].text.startswith("Every contract")
