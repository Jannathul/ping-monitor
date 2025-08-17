from flask import Flask, render_template
import mysql.connector
import json
import os

app = Flask(__name__)

# Load DB config from JSON
CONFIG_PATH = os.path.join("config", "db_config.json")
with open(CONFIG_PATH, "r") as f:
    db_config = json.load(f)

def get_failed_once_logs():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ip_address,
                   MIN(timestamp) AS failure_start
            FROM ping_logs
            WHERE status = 'failure'
              AND (
                  timestamp > (
                      SELECT MAX(timestamp)
                      FROM ping_logs AS s
                      WHERE s.status = 'success'
                        AND s.ip_address = ping_logs.ip_address
                  )
                  OR NOT EXISTS (
                      SELECT 1
                      FROM ping_logs AS s
                      WHERE s.status = 'success'
                        AND s.ip_address = ping_logs.ip_address
                  )
              )
            GROUP BY ip_address;
        """)
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        return logs
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return []

@app.route("/")
def index():
    logs = get_failed_once_logs()
    return render_template("index.html", logs=logs)

if __name__ == "__main__":
    app.run(debug=True)