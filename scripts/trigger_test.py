import datetime
import os

try:
    # Absolute path to avoid ambiguity
    log_path = os.path.join(os.path.dirname(__file__), "trigger_check.txt")
    with open(log_path, "a") as f:
        f.write(f"Triggered at {datetime.datetime.now()}\n")
except Exception as e:
    # Fail-fast logging
    error_path = os.path.join(os.path.dirname(__file__), "error_log.txt")
    with open(error_path, "a") as f:
        f.write(f"Error at {datetime.datetime.now()}: {str(e)}\n")