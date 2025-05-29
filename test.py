import jwt
import os
from dotenv import load_dotenv

load_dotenv()  # This will load .env into os.environ
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

payload = {"fleet_id": 3}
token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(token)
