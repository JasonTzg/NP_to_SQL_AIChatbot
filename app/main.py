from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .db import get_connection
from .openai_utils import get_sql_from_openai

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.post("/query")
def run_query(request: QueryRequest):
    try:
        sql = get_sql_from_openai(request.query)
        print(f"[Generated SQL] {sql}")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                colnames = [desc.name for desc in cur.description]
                return {"sql": sql, "results": [dict(zip(colnames, row)) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
