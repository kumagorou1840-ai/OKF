@echo off
chcp 65001 > nul
echo ==============================================
echo [1/3] 社員Aの日報を生成中...
echo ==============================================
python "C:\Users\PC_User\Documents\Obsidian\obsidian_1\AI_Office\Employee_A\generate_report.py"

echo.
echo ==============================================
echo [2/3] 社員5体による自律議論を開始中...
echo ==============================================
python "C:\Users\PC_User\Documents\Obsidian\obsidian_1\AI_Office\Secretary\discussion.py"

echo.
echo ==============================================
echo [3/3] 秘書AIが議論を回収・サマリー生成中...
echo ==============================================
python "C:\Users\PC_User\Documents\Obsidian\obsidian_1\AI_Office\Secretary\secretary.py"

echo.
echo ==============================================
echo 全てのオフィス業務処理が完了しました！
echo Obsidianを確認してください。
echo ==============================================
pause