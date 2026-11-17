@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

echo ====================================================================
echo [0/2] Checking port 8501 for existing Streamlit instance...
echo ====================================================================
netstat -ano | findstr ":8501" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Dashboard is already running on port 8501.
    echo [INFO] Skipping ETL sync to avoid DuckDB lock conflict and opening browser...
    start "" "http://localhost:8501"
    exit /b 0
)

echo ====================================================================
echo [1/2] Running ETL sync: SQLite -> DuckDB...
echo ====================================================================
".venv\Scripts\python.exe" src\etl_sync.py
if errorlevel 1 (
    echo [ERROR] ETL sync failed. Check logs\app.log
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo [2/2] Starting Streamlit dashboard...
echo ====================================================================
".venv\Scripts\python.exe" -m streamlit run app.py
pause
