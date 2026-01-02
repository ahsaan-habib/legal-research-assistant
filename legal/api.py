"""uvicorn legal.api:app --port 8040"""
from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI
from pydantic import BaseModel

from . import retrieve
from .consult import consult
from .present import render

app = FastAPI(title="legal-research-assistant")


class Ask(BaseModel):
    description: str
    jurisdiction: str | None = None


@app.get("/jurisdictions")
def jurisdictions() -> list[str]:
    return retrieve.jurisdictions()


@app.post("/consult")
def post_consult(body: Ask) -> dict:
    c = consult(body.description, body.jurisdiction)
    return {"status": c.status, "message": render(c), "detail": asdict(c)}
