import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.get("/pmo")
print(response.status_code)
print(response.headers)
