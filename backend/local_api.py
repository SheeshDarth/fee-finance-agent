from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent_runner import build_finance_run
from data_import import merge_import_data


class LocalRunRequest(BaseModel):
    asOf: str = "2026-08-13"
    datasets: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


app = FastAPI(title="FeeOps Local Import API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(127\.0\.0\.1|localhost):\d+",
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/runs")
def run_imported_finance_workflow(request: LocalRunRequest) -> dict[str, Any]:
    try:
        as_of = date.fromisoformat(request.asOf)
        merged_data = merge_import_data(request.datasets)
        return build_finance_run(as_of, use_llm=False, override_data=merged_data)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
