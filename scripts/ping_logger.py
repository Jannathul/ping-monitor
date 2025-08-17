# -*- coding: utf-8 -*-
import mysql.connector, datetime, time, json, threading, sys
from ping3 import ping as native_ping

# ---------- Load IP List ----------
def load_ip_list(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

# ---------- IP Validation ----------
def ip_addr_valid(iplist):
    for ip in iplist:
        octets = ip.split('.')
        if (len(octets) == 4 and
            1 <= int(octets[0]) <= 223 and
            int(octets[0]) != 127 and
            not (int(octets[0]) == 169 and int(octets[1]) == 254) and
            all(0 <= int(octet) <= 255 for octet in octets[1:])):
            continue
        else:
            print(f"Invalid IP detected: {ip}")
            sys.exit("Exiting due to invalid IP address.")

# ---------- Load DB Config ----------
def load_db_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# ---------- Multi-Packet Ping ----------
def ping_multiple(ip, count=3, timeout=5):
    latencies = []
    for _ in range(count):
        try:
            latency = native_ping(ip, timeout=timeout)
            if latency is not None:
                latencies.append(latency)
        except:
            continue
    if latencies:
        avg_latency = round(sum(latencies) / len(latencies) * 1000, 2)  # ms
        return "success", avg_latency
    else:
        return "failure", None

# ---------- Log to DB ----------
def log_to_db(ip, status, latency, db_config):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO ping_logs (ip_address, status, timestamp, latency_ms) VALUES (%s, %s, %s, %s)",
            (ip, status, timestamp, latency)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass  # Optional: log to file if DB fails

# ---------- Ping + Log ----------
def ping_and_log(ip, db_config):
    status, latency = ping_multiple(ip)
    log_to_db(ip, status, latency, db_config)

# ---------- Main Loop ----------
def main():
    ip_list = load_ip_list("./config/ip_list.txt")
    ip_addr_valid(ip_list)
    db_config = load_db_config("./config/db_config.json")
    ping_interval = 300  # seconds

    while True:
        threads = []
        for ip in ip_list:
            t = threading.Thread(target=ping_and_log, args=(ip, db_config))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        time.sleep(ping_interval)

if __name__ == "__main__":
    main()