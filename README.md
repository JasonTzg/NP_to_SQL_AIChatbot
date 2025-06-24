# NP_to_SQL_AIChatbot

AI Chatbot Assistant to support natural language QnA powered by LLM (gpt-4.1-nano). Converts plain-English queries into SQL against some dataset, and return a concise, human-readable answers.

## 🚀 Demo (Hosted on Render) until 27 June 2025

- **Health check**: [`https://np-to-sql-aichatbot.onrender.com/ping`](https://np-to-sql-aichatbot.onrender.com/ping)
- **Query endpoint**: `/chat`
- **Website**: [`https://np-to-sql-aichatbot.onrender.com/`](https://np-to-sql-aichatbot.onrender.com/) (See below for screenshots if after 27 June)

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
curl -X POST https://np-to-sql-aichatbot.onrender.com/chat ^
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

Please look at the test_query_results.csv for all the test completed in test_query.py.  
$${\color{green}26/30}$$ Tests passed overall.  $${\color{orangered} 4 }$$ tests not get converted from NP to SQL using gpt-4.1-nano.  
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

---

## 🖼️ Frontend Screenshots & How It Works

Below are screenshots of the web frontend for NP_to_SQL_AIChatbot:

### 1. Arrival on Website
![Website Interface Screenshot](/pictures/initial.png)
- **Designing:** A quick designing of the frontend using a blend of purple, pink, and yellow. 

### 2. Query to the Chatbot to draw data out from Database and answer the user in a human-readable format.
![SQL and Results Screenshot](/pictures/send_requests.png)
- **How it works:** User selects the fleetid (act as after login, each user will have an assigned fleetid), then User types on what to ask about their vehicle. Such as 'numbers of vehicle or/and numbers of those vehicle vin', 'total distance travelled for each vehicle', 'right now my fleet has how many vehicles', etc.
- **How will it reply:** For transparency, the generated SQL and raw database results are shown in the History tab. The human-readable text result from chatbot will be displayed under the Ask Assistant column and also the History tab in each corresponding History card. 

### 3. Simple drag and drop - Reordering
![Reordering of History Card Screenshot](/pictures/reordering_fav_history.png)
- **How it works:** User just click and hold to drag and move the Favourite History Card to the top for more easy view. Subsequently in the future, if needed, we can create a Favourite column to save all the users selected History Card. 

### 4. Selecting another fleet - Acting as Logging in with different user
![Fleet 3 Screenshot](/pictures/trying_other_fleets.png)
- **How it works:** By selecting another fleet, you will be able to access data only in those related fleet regardless of what you prompt the Assistant. Fleet 1 will only see vehicles' data that is relevant to Fleet id 1. 

### 5. Testing on Fleet 3 which contains no data
![Fleet 3 prompting Screenshot](/pictures/fleet3_novehicle.png)
- **How it works:** Prompting the Assistant to help me retrieve vehicle data that is/are under Fleet 3. Which can be seen at the last History Card. 

### 6. History Card Explanation
![Examples of History Cards Screenshot](/pictures/history_cards.png)
- **How it works:** Each History card contains - _User Prompt_, _SQL_ converted from User Prompt, _SQL Result_ that went through the Database, and the _Text Response_ from the chatbot.
- **Why:** This will show clearly to the company on what requests will trigger what type of SQL statement. Allow the company to improve on the system in the future, making it less breakable and more efficient. 

---