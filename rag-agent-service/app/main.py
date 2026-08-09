from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, validator


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from agent.agent_runner import run_agent
from tools.pesticide_query import query_active_substance


app = FastAPI()


class AgentQueryRequest(BaseModel):
    question: str

    @validator("question")
    def question_must_not_be_empty(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("question must be a non-empty string")
        return value.strip()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/active-substance")
def active_substance(pesticide_name: str = Query(...)) -> dict[str, object]:
    try:
        active_substances = query_active_substance(pesticide_name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Neo4j 查询失败: {exc}") from exc

    return {
        "pesticide_name": pesticide_name,
        "active_substances": active_substances,
    }


@app.post("/agent/query")
def agent_query(request: AgentQueryRequest) -> dict[str, object]:
    try:
        result = run_agent(request.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent 查询失败: {exc}") from exc

    return {
        "question": request.question,
        "answer": result.get("answer", ""),
        "tool_trace": result.get("tool_trace", []),
        "execution_state": result.get("execution_state", {}),
    }
