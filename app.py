import os
import calendar
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from odoo_client import push_timesheet_to_odoo, get_employees, get_projects

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-flask-key")

@app.route("/")
def index():
    now = datetime.now()
    year = int(request.args.get("year", now.year))
    month = int(request.args.get("month", now.month))
    
    num_days = calendar.monthrange(year, month)[1]
    days = [f"{year}-{month:02d}-{d:02d}" for d in range(1, num_days + 1)]
    
    try:
        employees = get_employees()
        projects = get_projects()
    except Exception as e:
        print("Error connecting to Odoo:", e)
        employees = []
        projects = []
    
    return render_template("index.html", year=year, month=month, days=days, employees=employees, projects=projects)

@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    employee_id = int(data.get("employee_id")) 
    project_id = int(data.get("project_id")) 
    task_id = data.get("task_id", False)
    entries = data.get("entries", [])
    
    try:
        push_timesheet_to_odoo(employee_id, project_id, task_id, entries)
        return jsonify({"status": "success", "message": "Timesheet successfully pushed to Odoo!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)
