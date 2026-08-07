from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, Query


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from tools.pesticide_query import query_active_substance


app = FastAPI()


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