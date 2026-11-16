@echo off
chcp 65001 > nul
title YouTube Summary Watcher Loop
echo ========================================================
echo   YouTube Summary Watcher (Loop Engineering Outer Loop)
echo ========================================================
echo.
cd /d "%~dp0\.."

if exist ".venv\Scripts\python.exe" (
    echo [.venv] Python環境を使用して常駐監視ループを開始します...
    .venv\Scripts\python.exe scripts\process_youtube_summaries.py --watch
) else (
    echo [System] Python環境を使用して常駐監視ループを開始します...
    python scripts\process_youtube_summaries.py --watch
)

pause
