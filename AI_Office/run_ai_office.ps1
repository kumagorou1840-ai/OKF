Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "[1/3] 社員Aの日報を生成中..." -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
python "C:\Users\PC_User\Documents\Obsidian\obsidian_1\AI_Office\Employee_A\generate_report.py"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Yellow
Write-Host "[2/3] 社員5体による自律議論を開始中..." -ForegroundColor Yellow
Write-Host "==============================================" -ForegroundColor Yellow
python "C:\Users\PC_User\Documents\Obsidian\obsidian_1\AI_Office\Secretary\discussion.py"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "[3/3] 秘書AIが議論を回収・サマリー生成中..." -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
python "C:\Users\PC_User\Documents\Obsidian\obsidian_1\AI_Office\Secretary\secretary.py"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Magenta
Write-Host "すべてのオフィス業務処理が完了しました！" -ForegroundColor Magenta
Write-Host "Obsidianを確認してください。" -ForegroundColor Magenta
Write-Host "==============================================" -ForegroundColor Magenta