@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

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
