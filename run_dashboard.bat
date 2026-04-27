@echo off
cd /d "%~dp0"
echo ============================================
echo   3D Print Stats - Fetching latest data...
echo ============================================
python fetch_stats.py
echo.
echo Opening dashboard...
start "" dashboard.html
