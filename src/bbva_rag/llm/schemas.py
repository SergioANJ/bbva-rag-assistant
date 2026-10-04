"""Resultados estructurados solicitados al LLM."""

from typing import Literal

from pydantic import BaseModel, Field


class QueryAnalysis(BaseModel):
    intent: Literal["bank_query", "greeting", "out_of_scope"] = Field(
        description="bank_query: question about the bank; greeting: hello/thanks/bye with no "
        "question; out_of_scope: unrelated topics or personalized financial advice"
    )
    standalone_question: str = Field(
        description="The question rewritten so it can be understood without the history"
    )
    reply: str | None = Field(
        default=None,
        description="Short reply in Spanish, only for greeting or out_of_scope",
    )
