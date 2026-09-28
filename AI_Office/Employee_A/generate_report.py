import os
import requests

VAULT_PATH = "./"
LOG_FILE = os.path.join(VAULT_PATH, "AI_Office/Employee_A/work_log.txt")
OUTPUT_REPORT = os.path.join(VAULT_PATH, "AI_Office/Employee_A/2026-09-26_Report.md")
OLLAMA_MODEL = "ornith-9b:latest"

# 1. 走り書きの作業ログを読み込む
with open(LOG_FILE, "r", encoding="utf-8") as f:
    work_log = f.read()

# 2. 社員Aのペルソナプロンプト
prompt = f"""
あなたはWebリサーチおよび市場分析を担当するAI社員（社員A）です。
以下の日中の作業ログを元に、上司へ提出するフォーマット通りの「業務日報Markdown」を作成してください。

【出力フォーマット】
# 日報: 社員A（リサーチ担当）
日付: 2026-09-26

## 本日の業務内容
- （作業ログから具体的に箇条書き）

## 発生した課題・相談事項
- （課題や上司の判断が必要な事項を箇条書き）

## 明日の予定
- （明日の予定を箇条書き）

【作業ログ】
{work_log}
"""

# 3. Ollama API呼び出し
res = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
)
report_content = res.json()["response"]

# 4. 日報Markdownとして書き出し
with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
    f.write(report_content)

print("社員Aの日報が自動生成されました。")
