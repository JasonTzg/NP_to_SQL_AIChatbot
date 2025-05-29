from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.openai_utils import get_sql_from_openai, get_readabletext_from_openai
from dotenv import load_dotenv
from openai import OpenAI
import psycopg
import os

load_dotenv()  # This will load .env into os.environ

# Initialize FastAPI app and OpenAI client
app = FastAPI()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
)

class QueryRequest(BaseModel):
    query: str

def get_connection():
    return psycopg.connect(os.getenv("DATABASE_URL", ""), autocommit=True)

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.post("/query")
def run_query(request: QueryRequest):
    try:
        sql = get_sql_from_openai(request.query, client)
        # sql = "SELECT * FROM raw_telemetry WHERE vehicle_id = (SELECT vehicle_id FROM vehicles WHERE registration_no = 'GBM6296G') ORDER BY ts DESC LIMIT 1;"
        print(f"[Generated SQL] {sql}")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                colnames = [desc.name for desc in cur.description]
                
                text_results = [dict(zip(colnames, row)) for row in rows]
                
                human_readable_text = get_readabletext_from_openai(request.query, sql, text_results, client)
                return human_readable_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
