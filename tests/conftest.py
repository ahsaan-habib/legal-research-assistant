"""Offline by default: fake embedder, temp index over the fictional Examplia
corpus plus a second jurisdiction, scripted model. test_smoke_ollama.py is
opt-in."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
_tmp = Path(tempfile.mkdtemp(prefix="legal-test-"))
os.environ.setdefault("LEGAL_INDEX_DIR", str(_tmp / "chroma"))
shutil.copytree(Path(__file__).resolve().parents[1] / "corpus", _tmp / "corpus")
(_tmp / "corpus" / "other").mkdir()
(_tmp / "corpus" / "other" / "tenancy.md").write_text(
    "---\njurisdiction: zz\ninstrument: Otherland Housing Act 2001\n---\n"
    "## Section 2 — Deposits\nA landlord may take a deposit of up to six months' rent in Otherland.\n")
os.environ.setdefault("LEGAL_CORPUS", str(_tmp / "corpus"))

import fake_st  # noqa: E402

fake_st.install()

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def indexed():
    from legal import retrieve

    return retrieve.index()


class ScriptedLLM:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def __call__(self, messages, fmt=None):
        self.calls.append({"messages": messages, "fmt": fmt})
        return self.replies.pop(0)


@pytest.fixture
def llm(monkeypatch):
    def install(*replies):
        fake = ScriptedLLM(*replies)
        monkeypatch.setattr("legal.llm.chat", fake)
        return fake
    return install
