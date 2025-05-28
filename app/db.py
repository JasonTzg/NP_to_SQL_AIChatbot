import psycopg
from .config import DB_URL

def get_connection():
    return psycopg.connect(DB_URL, autocommit=True)
