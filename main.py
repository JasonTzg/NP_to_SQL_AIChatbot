from fastapi import FastAPI, HTTPException, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel
from app.openai_utils import get_sql_from_openai, get_readabletext_from_openai # from openaiutils file
from app.auth_utils import get_current_fleet_id, check_sql                      # from authutils file
from dotenv import load_dotenv
from openai import OpenAI
import psycopg
import os

load_dotenv()  # This will load .env into os.environ

# Initialize FastAPI, OpenAI client, and JWT secret
app = FastAPI()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", ""),
)
jwt_secret = os.getenv("JWT_SECRET")

class QueryRequest(BaseModel):
    query: str

# In DB utils. But for simplicity, we define it here.
def get_connection():
    return psycopg.connect(os.getenv("DATABASE_URL", ""), autocommit=True)

# Check if the curl to backend is working
@app.get("/ping")
def ping():
    return {"status": "ok"}

# Endpoint to run the query task
@app.post("/chat")
def run_query(request: QueryRequest, fleet_id: int = Depends(get_current_fleet_id(jwt_secret))):
    try:
        sql = get_sql_from_openai(request.query, client, fleet_id)
        print(f"[Generated SQL] {sql}")
        check_sql(sql, fleet_id)
        print(f"[SQL safe]")
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                colnames = [desc.name for desc in cur.description]
                
                text_results = [dict(zip(colnames, row)) for row in rows]
                
                human_readable_text = get_readabletext_from_openai(request.query, sql, text_results, client)
                return {
                        "sql": sql,
                        "raw_results": text_results,
                        "human_readable_text": human_readable_text,
                    }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
