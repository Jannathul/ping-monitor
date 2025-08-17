@echo off

REM ✅ Launch Flask App 1 (report)
start "" "C:\Users\FIRDOUSE\AppData\Local\Programs\Python\Python313\pythonw.exe" "C:\Users\FIRDOUSE\project\ping-monitor\report\app.py"

REM ✅ Launch Flask App 2 (dashboard)
start "" "C:\Users\FIRDOUSE\AppData\Local\Programs\Python\Python313\pythonw.exe" "C:\Users\FIRDOUSE\project\ping-monitor\dashboard\app.py"

REM 🕒 Optional: Wait a few seconds for servers to start (not strictly required)
timeout /t 3 /nobreak >nul

REM 🌐 Open dashboards in browser
start "" "http://localhost:5001/report"
start "" "http://localhost:5000"

exit
