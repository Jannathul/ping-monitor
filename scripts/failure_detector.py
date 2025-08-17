import mysql.connector, json, os
from datetime import datetime, timedelta
from collections import defaultdict

def load_db_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'db_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def detect_failures():
    cfg = load_db_config()
    conn = mysql.connector.connect(**cfg)
    cursor = conn.cursor(dictionary=True)

    cutoff = datetime.now() - timedelta(minutes=15)
    cursor.execute("""
        SELECT ip_address, status FROM ping_logs
        WHERE timestamp >= %s
        ORDER BY ip_address, timestamp DESC
    """, (cutoff,))

    logs_by_ip = defaultdict(list)
    for row in cursor.fetchall():
        logs_by_ip[row['ip_address']].append(row['status'].lower())

    failures = {}
    for ip, statuses in logs_by_ip.items():
        recent = statuses[:10]
        if recent[:3] == ['failure'] * 3:
            failures[ip] = 'CRITICAL'
        elif recent.count('failure') >= 5:
            failures[ip] = 'UNSTABLE'
        elif recent.count('flaky') >= 5:
            failures[ip] = 'FLAKY'
        elif len(recent) == 0:
            failures[ip] = 'OFFLINE'
        elif recent.count('failure') >= 2:
            failures[ip] = 'INTERMITTENT'

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failure Summary:")
    for ip, status in failures.items():
        print(f"  {ip:<15} → {status}")

    conn.close()

if __name__ == "__main__":
    detect_failures()
