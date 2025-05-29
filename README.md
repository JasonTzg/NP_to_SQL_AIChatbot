# NP_to_SQL_AIChatbot

AI Chatbot Assistant to support natural language QnA powered by LLM (gpt-4.1-nano). Converts plain-English queries into SQL against some dataset, and return a concise, human-readable answers.

## 🚀 Demo (Hosted on Render)

- **Health check**: [`https://np-to-sql-aichatbot.onrender.com/ping`](https://np-to-sql-aichatbot.onrender.com/ping)
- **Query endpoint**: `/chat`

## 🔐 Authentication

All requests require a JWT token with a `fleet_id` claim.  
JWT authentication with fleet_id row-level enforcement  
Post-LLM SQL inspection on WHERE clause to block injection patterns (WHERE fleet_id = 1 or 2=2 etc.)  
Post-LLM SQL inspection to block injection patterns (;, --, DROP, etc.)  
Reject queries missing proper WHERE fleet_id = X

## 🧪 Example Request (via curl)

fleet_id 1 token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmbGVldF9pZCI6MX0.DLzkE0mnFbNTEN1MPcBC7ywxZxVtDPYe23oasblELn0  
fleet_id 2 token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmbGVldF9pZCI6Mn0.7eMYokNtpIbVrVQjL6xP3_bYqJbkO4cOqxKb29T1eNw  
fleet_id 3 (does not have any data) token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmbGVldF9pZCI6M30.4uZe5wr4BRbJbF-V9mW3-HFBnzhlIOG37tpXL8HpnnI  

```bash
curl -X POST http://localhost:8000/chat ^
-H "Authorization: Bearer <any_token_above>" ^
-H "Content-Type: application/json" ^
-d "{\"query\": \"How many SRM T3 EVs are in my fleet?\"}"
```

### Expected Response:
```json
{
    "sql":"SELECT COUNT(*) \nFROM vehicles \nWHERE fleet_id = 1 \n  AND model = 'SRM T3'",
    "raw_results":[{"count":2}],
    "human_readable_text":"You have 2 SRM T3 EVs in your fleet."
}
```
--> For only fleet 1 token. Fleet 2 and 3 token does not have any SRM T3 EVs in their fleet.

Please look at the test_query_results.csv for all the test completed in test_query.py. 26/30 Tests passed overall. 4 tests did not get converted from NP to SQL using gpt-4.1-nano.  
All unit test for auth_utils.py is done in test_auth_utils.py. All passes.

---

## ⚡ Quick Setup for yourself (<5 mins)

```bash
git clone https://github.com/JasonTzg/NP_to_SQL_AIChatbot.git
cd NP_to_SQL_AIChatbot
venv/Scripts/activate
pip install -r requirements.txt

# Set your environment variables
export OPENAI_API_KEY=...
export JWT_SECRET=...
export DATABASE_URL=...

# Run server
python -m uvicorn main:app --
```