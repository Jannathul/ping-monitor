CREATE DATABASE IF NOT EXISTS ping_monitor;
USE ping_monitor;

CREATE TABLE IF NOT EXISTS ping_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    status ENUM('success', 'failure', 'flaky') NOT NULL,
    latency_ms FLOAT,
    INDEX(ip_address),
    INDEX(timestamp)
);

SELECT * FROM ping_logs;
