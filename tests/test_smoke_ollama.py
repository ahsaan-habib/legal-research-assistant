"""Issue-spotting and a gated answer from a real local model. Opt-in:

    RUN_OLLAMA=1 pytest tests/test_smoke_ollama.py -s
"""
import functools
import os

import pytest

from legal import retrieve
from legal.consult import consult
from legal.present import render

pytestmark = pytest.mark.skipif(os.environ.get("RUN_OLLAMA") != "1", reason="set RUN_OLLAMA=1 to run")


def test_asks_for_jurisdiction_then_answers_or_refuses(indexed, monkeypatch):
    # the tests index with a bag-of-words stand-in for bge-small, which scores lower
    monkeypatch.setattr(retrieve, "search", functools.partial(retrieve.search, min_score=0.2))
    c = consult("I moved out of my flat six weeks ago and my landlord still hasn't returned my deposit.")
    print("\n", render(c))
    assert c.status == "need_jurisdiction" and c.issues
    c = consult("I moved out of my flat six weeks ago and my landlord still hasn't returned my deposit.", "EX")
    print("\n", render(c))
    assert c.status in ("answered", "refused")
    if c.status == "answered":
        assert c.citations and all("Examplia" in x for x in c.citations)
