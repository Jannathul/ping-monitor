from flask import Flask, render_template, request, send_file
from datetime import datetime
import mysql.connector
import csv
import io
import os
import json

app = Flask(__name__)

# Load DB config
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "db_config.json"))
with open(CONFIG_PATH, "r") as f:
    db_config = json.load(f)

def get_db_connection():
    return mysql.connector.connect(**db_config)

def fetch_logs(range_type):
    date_filter = {
        "daily": "DATE(timestamp) = CURDATE()",
        "weekly": "timestamp >= CURDATE() - INTERVAL 7 DAY",
        "monthly": "timestamp >= CURDATE() - INTERVAL 30 DAY"
    }.get(range_type, "DATE(timestamp) = CURDATE()")

    query = f"""
        SELECT ip_address, status, timestamp
        FROM ping_logs
        WHERE {date_filter}
        ORDER BY ip_address, timestamp
    """

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    logs = cursor.fetchall()
    conn.close()
    return logs

def fetch_logs_for_long_standing():
    query = """
        SELECT ip_address, status, timestamp
        FROM ping_logs
        WHERE timestamp >= CURDATE() - INTERVAL 30 DAY
        ORDER BY ip_address, timestamp
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_long_standing_sessions():
    logs = fetch_logs_for_long_standing()
    sessions = group_failure_sessions(logs)

    # Track latest success timestamp per IP
    recent_success = {}
    for log in logs:
        if log['status'] == 'success':
            ip = log['ip_address']
            ts = log['timestamp']
            if ip not in recent_success or ts > recent_success[ip]:
                recent_success[ip] = ts

    latest_unresolved = {}
    for s in sessions:
        ip = s['ip_address']
        if s['still_failing'] and s['days_failed'] >= 1:
            # Exclude if there's a success after failure_start
            if ip in recent_success and recent_success[ip] > s['failure_start']:
                continue
            if ip not in latest_unresolved or s['failure_start'] > latest_unresolved[ip]['failure_start']:
                latest_unresolved[ip] = s

    return list(latest_unresolved.values())

@app.route("/report")
def report():
    range_type = request.args.get("range", "daily").lower()
    export = request.args.get("export", "false").lower()
    long_only = request.args.get("long", "false").lower() == "true"

    if long_only:
        sessions = get_long_standing_sessions()
    else:
        raw_logs = fetch_logs(range_type)
        sessions = group_failure_sessions(raw_logs)

    if export == "true" and sessions:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "ip_address", "failure_start", "failure_end", "hours_failed", "days_failed"
        ])
        writer.writeheader()
        for s in sessions:
            row = {
                "ip_address": s["ip_address"],
                "failure_start": s["failure_start"].strftime('%Y-%m-%d %H:%M:%S'),
                "failure_end": (
                    s["failure_end"].strftime('%Y-%m-%d %H:%M:%S')
                    if isinstance(s["failure_end"], datetime)
                    else "ONGOING"
                ) if s["failure_end"] else "ONGOING",
                "hours_failed": s["hours_failed"],
                "days_failed": s["days_failed"]
            }
            writer.writerow(row)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            download_name=f"{range_type}_failures_{datetime.now().strftime('%Y%m%d')}.csv",
            as_attachment=True
        )

    return render_template("report.html", logs=sessions, range_type=range_type, long_only=long_only)

def group_failure_sessions(logs):
    sessions = []
    ip_events = {}

    for log in logs:
        ip = log['ip_address']
        ip_events.setdefault(ip, []).append(log)

    for ip, events in ip_events.items():
        session_start = None

        for event in events:
            status = event['status']
            ts = event['timestamp']

            if status == 'failure':
                if session_start is None:
                    session_start = ts

            elif status == 'success' and session_start:
                duration = (ts - session_start).total_seconds()
                sessions.append({
                    'ip_address': ip,
                    'failure_start': session_start,
                    'failure_end': ts,
                    'hours_failed': round(duration / 3600, 2),
                    'days_failed': round(duration / 86400, 2),
                    'still_failing': False
                })
                session_start = None

        if session_start:
            now = datetime.now()
            duration = (now - session_start).total_seconds()
            sessions.append({
                'ip_address': ip,
                'failure_start': session_start,
                'failure_end': None,
                'hours_failed': round(duration / 3600, 2),
                'days_failed': round(duration / 86400, 2),
                'still_failing': True
            })

    return sessions

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)