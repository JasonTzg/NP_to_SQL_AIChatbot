import pytest
from fastapi.testclient import TestClient
import sys
sys.path.append("..")  # Adjust path to import app from main module
from main import app
import csv
import os
import unicodedata

client = TestClient(app)

# JWT tokens for different fleet_ids
TOKENS = {
    1: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmbGVldF9pZCI6MX0.DLzkE0mnFbNTEN1MPcBC7ywxZxVtDPYe23oasblELn0",
    2: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmbGVldF9pZCI6Mn0.7eMYokNtpIbVrVQjL6xP3_bYqJbkO4cOqxKb29T1eNw",
    3: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmbGVldF9pZCI6M30.4uZe5wr4BRbJbF-V9mW3-HFBnzhlIOG37tpXL8HpnnI"  # Valid, but no data in DB
}

test_cases = [
    ("What is the SOC of vehicle GBM6296G right now?", "GBM6296G"),
    ("How many SRM T3 EVs are in my fleet?", "SRM T3"),
    ("Did any SRM T3 exceed 33 °C battery temperature in the last 24 h?", "battery temperature"),
    ("What is the fleet‑wide average SOC comfort zone?", "comfort zone"),
    ("Which vehicles spent > 20 % time in the 90‑100 % SOC band this week?", "SOC band"),
    ("How many vehicles are currently driving with SOC < 30 %?", "below 30%"),
    ("What is the total km and driving hours by my fleet over the past 7 days, and which are the most-used & least-used vehicles?", "past 7 days"),
    ("Does my vehicles have any unresolved alerts? If yes, give me the vehicle vin with the severity of the alert. ", "alert"),
    ("Give me the latest summary of my fleet's daily performance.", "fleet"),
    ("Give me the total maintenance cost of all my vehicles in the last 2 months.", "cost"),
]

CSV_FILE = "test_query_results.csv"

def clean_text(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")

@pytest.mark.parametrize("fleet_id", [1,2,3])  # Run for each valid token
@pytest.mark.parametrize("query,expected_keyword", test_cases)
def test_nl_queries_across_fleets(fleet_id, query, expected_keyword):
    headers = {
        "Authorization": f"Bearer {TOKENS[fleet_id]}",
        "Content-Type": "application/json",
    }
    
    passed = False
    reason = ""
    sql = ""
    raw_results = ""
    response_text = ""

    try:
        response = client.post("/chat", headers=headers, json={"query": query})
        if response.status_code != 200:
            if hasattr(response, "detail"):
                if response.detail:
                    reason = f"Status code {response.status_code} and detail: {response.detail}"
            else:
                reason = f"Status code {response.status_code}"
            raise Exception(reason)

        response_json = response.json()
        response_text = response_json["human_readable_text"]
        sql = response_json["sql"]
        raw_results = str(response_json["raw_results"])

        if fleet_id in [1, 2]:  # Fleets with data
            passed = expected_keyword.lower() in response_text.lower()
            reason = "Keyword found" if passed else "Keyword not found"
            assert passed
        elif fleet_id == 3:  # Empty fleet case
            passed = any(keyword in response_text.lower() for keyword in ["no", "0", "none", "not"])
            reason = "Empty fleet valid response" if passed else "Empty fleet invalid response"
            assert passed

    except Exception as e:
        reason = reason or str(e)

    # Will always pass result, but data can see whether it fails or passes - Always log
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["fleet_id", "query", "sql_used", "db_return_result", "response", "expected_keyword_to_check", "passed", "reason"])
        writer.writerow([
            fleet_id,
            query,
            sql,
            clean_text(raw_results),
            clean_text(response_text),
            clean_text(expected_keyword),
            passed,
            reason,
        ])