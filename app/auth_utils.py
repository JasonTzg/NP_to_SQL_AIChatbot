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

def extract_where_clause(sql: str) -> str:
    # Define regex for matching clause keywords that can follow WHERE
    clause_keywords = r"\b(AND|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|UNION|EXCEPT|INTERSECT)\b"

    sql_lower = sql.lower()
    where_match = re.search(r"\bwhere\b", sql_lower)
    if not where_match:
        return ""  # no WHERE clause

    start = where_match.start()

    # Search for the next clause keyword after WHERE
    next_clause_match = re.search(clause_keywords, sql[start:], re.IGNORECASE) # added re.IGNORECASE to match case-insensitively
    if next_clause_match:
        end = start + next_clause_match.start()
    else:
        end = len(sql)  # no further clause, take till the end

    where_clause = sql[start:end].strip()
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
    # check_sql_and_where_for_disallowed(sql, where_clause, allowed_fleet_id)
    
    return True