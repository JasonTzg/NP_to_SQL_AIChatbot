from fastapi.security import HTTPBearer
from fastapi import HTTPException, Request
import os
import re
import jwt

ALGORITHM = "HS256"
security = HTTPBearer()

def decode_jwt(token: str, jwt_key):
    try:
        payload = jwt.decode(token, jwt_key, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")

def get_current_fleet_id(jwt_secret: str):
    def dependency(request: Request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")

        token = auth_header[len("Bearer "):]
        payload = decode_jwt(token, jwt_secret)
        fleet_id = payload.get("fleet_id")
        if not fleet_id:
            raise HTTPException(status_code=403, detail="Fleet ID not found in token")
        return fleet_id
    return dependency

# find the WHERE clause in SQL and find the first 'fleet_id', then from the 'fleet_id' find the next clause keyword (AND, GROUP BY, ORDER BY, etc.) and return from the start of 'fleet_id' to the end of that clause 
def extract_where_clause(sql: str) -> str:
    # Lowercase for searching, but keep original for extraction
    sql_lower = sql.lower()
    where_match = re.search(r"\bwhere\b", sql_lower)
    if not where_match:
        return ""  # no WHERE clause

    start = where_match.start()

    # Find 'fleet_id' after WHERE
    fleet_id_match = re.search(r"fleet_id\s*=\s*\d+", sql_lower[start:])
    if not fleet_id_match:
        return ""  # fleet_id not found
    
    clause_keywords = r"\b(AND|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|UNION|EXCEPT|INTERSECT)\b"
    next_clause_match = re.search(clause_keywords, sql_lower[start + fleet_id_match.end():], re.IGNORECASE)
    if next_clause_match:
        clause_end = start + fleet_id_match.end() + next_clause_match.start()
    else:
        clause_end = len(sql)
        
    # Extract from fleet_id=... up to next clause
    where_clause = sql[start + fleet_id_match.start():clause_end].strip()
    return where_clause

def check_sql_and_where_for_disallowed(sql:str, where_clause: str, allowed_fleet_id: int):
    # Check for disallowed patterns in the full SQL statement
    disallowed_sql = ["drop", "insert", "delete", "--", ";"]
    sql_lower = sql.lower()
    for pattern in disallowed_sql:
        if pattern in sql_lower:
            raise ValueError(f"Disallowed pattern '{pattern}' found in SQL statement")

    # Check for disallowed patterns in the WHERE clause
    disallowed_where = [" or ", " union ", " drop ", " insert ", " delete ", "--", ";"]
    where_lower = where_clause.lower()
    for pattern in disallowed_where:
        if pattern in where_lower:
            raise ValueError(f"Disallowed pattern '{pattern.strip()}' found in WHERE clause")

    # Check if fleet_id = allowed_fleet_id exists in the WHERE clause
    fleet_id_pattern = re.compile(r"fleet_id\s*=\s*(\d+)")
    fleet_ids = fleet_id_pattern.findall(where_lower)
    if not fleet_ids:
        raise ValueError("Missing fleet_id condition in WHERE clause")

    for fid in fleet_ids:
        if int(fid) != allowed_fleet_id:
            raise ValueError(f"Fleet ID mismatch: found {fid} but expected {allowed_fleet_id}")

    return True

def check_sql(sql: str, allowed_fleet_id: int) -> str:
    where_clause = extract_where_clause(sql)
    if not where_clause:
        raise ValueError("No WHERE clause found in SQL statement")
    
    try:
        check_sql_and_where_for_disallowed(sql, where_clause, allowed_fleet_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return True