import requests

payload = {
    "employee_id": 1,
    "project_id": 1,
    "entries": [{"date": "2026-06-01", "hours": "8", "description": "test"}]
}
try:
    res = requests.post("http://localhost:5000/submit", json=payload)
    print(res.status_code, res.text)
except Exception as e:
    print("Error:", e)
