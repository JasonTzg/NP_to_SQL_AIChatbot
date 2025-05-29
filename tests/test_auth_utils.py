import pytest
from fastapi import HTTPException, Request
from starlette.datastructures import Headers
from starlette.requests import Request as StarletteRequest
import sys
sys.path.append("..")  # Adjust path to import app from main module
from app.auth_utils import (
    decode_jwt,
    get_current_fleet_id,
    extract_where_clause,
    check_sql_and_where_for_disallowed,
    check_sql
)
import jwt
from unittest.mock import Mock

JWT_SECRET = "testsecret"
ALGORITHM = "HS256"

def create_token(fleet_id=None):
    payload = {}
    if fleet_id is not None:
        payload["fleet_id"] = fleet_id
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

# --- decode_jwt ---
def test_decode_jwt_valid():
    token = create_token(fleet_id=1)
    decoded = decode_jwt(token, JWT_SECRET)
    assert decoded["fleet_id"] == 1

def test_decode_jwt_invalid():
    with pytest.raises(HTTPException) as e:
        decode_jwt("invalid.token.value", JWT_SECRET)
    assert e.value.status_code == 403
    assert "Invalid token" in str(e.value.detail)

# --- get_current_fleet_id ---
def test_get_current_fleet_id_valid():
    token = create_token(fleet_id=42)
    headers = Headers({"Authorization": f"Bearer {token}"})
    scope = {"type": "http", "headers": headers.raw}
    request = StarletteRequest(scope)
    fleet_id = get_current_fleet_id(JWT_SECRET)(request)
    assert fleet_id == 42

def test_get_current_fleet_id_missing_token():
    headers = Headers({})
    scope = {"type": "http", "headers": headers.raw}
    request = StarletteRequest(scope)
    with pytest.raises(HTTPException) as e:
        get_current_fleet_id(JWT_SECRET)(request)
    assert e.value.status_code == 401

def test_get_current_fleet_id_no_fleet_in_token():
    token = create_token()
    headers = Headers({"Authorization": f"Bearer {token}"})
    scope = {"type": "http", "headers": headers.raw}
    request = StarletteRequest(scope)
    with pytest.raises(HTTPException) as e:
        get_current_fleet_id(JWT_SECRET)(request)
    assert e.value.status_code == 403
    assert "Fleet ID not found" in str(e.value.detail)

# --- extract_where_clause ---
def test_extract_where_clause_with_fleet_id():
    sql = "SELECT * FROM raw_telemetry WHERE fleet_id = 123 AND speed > 20"
    where = extract_where_clause(sql)
    assert "fleet_id = 123" in where

def test_extract_where_clause_without_fleet_id():
    sql = "SELECT * FROM data WHERE speed > 30"
    where = extract_where_clause(sql)
    assert "" in where

def test_extract_where_clause_none():
    sql = "SELECT * FROM telemetry"
    where = extract_where_clause(sql)
    assert where == ""

# --- check_sql_and_where_for_disallowed ---
def test_check_sql_and_where_valid():
    sql = "SELECT * FROM table WHERE fleet_id = 1 AND temp > 20"
    where = extract_where_clause(sql)
    assert check_sql_and_where_for_disallowed(sql, where, 1) is True

def test_check_sql_disallowed_keyword():
    sql = "DELETE FROM table WHERE fleet_id = 1"
    where = extract_where_clause(sql)
    with pytest.raises(ValueError):
        check_sql_and_where_for_disallowed(sql, where, 1)

def test_check_sql_where_disallowed_or():
    sql = "SELECT * FROM table WHERE fleet_id = 1 OR 1=1"
    where = extract_where_clause(sql)
    with pytest.raises(ValueError):
        check_sql_and_where_for_disallowed(sql, where, 1)

def test_check_sql_mismatched_fleet():
    sql = "SELECT * FROM table WHERE fleet_id = 999"
    where = extract_where_clause(sql)
    with pytest.raises(ValueError):
        check_sql_and_where_for_disallowed(sql, where, 1)

# --- check_sql ---
def test_check_sql_valid():
    sql = "SELECT * FROM cars WHERE fleet_id = 1 AND speed > 10"
    assert check_sql(sql, 1) is True

def test_check_sql_no_where():
    sql = "SELECT * FROM cars"
    with pytest.raises(ValueError) as e:
        check_sql(sql, 1)
    assert "No WHERE clause" in str(e.value)
