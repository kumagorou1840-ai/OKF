import os
import requests

# === 設定 ===
VAULT_PATH = "./"  # 必要に応じてVaultの絶対パスに変更
EMPLOYEE_FILE = os.path.join(VAULT_PATH, "AI_Office/Employee_A/2026-09-26_Report.md")
INBOX_FILE = os.path.join(VAULT_PATH, "AI_Office/Inbox/2026-09-26_Secretary_Summary.md")
OLLAMA_MODEL = "qwen2.5:7b"  # 使用するモデル名（gemma等でも可）

# 1. 社員の日報を読み込む
with open(EMPLOYEE_FILE, "r", encoding="utf-8") as f:
    daily_report = f.read()

# 2. 秘書AIへのプロンプト
prompt = f"""
あなたは優秀なAI秘書です。
以下の「社員Aの日報」を読み、オーナー（上司）への報告書を作成してください。

【報告書の必須項目】
1. 本日の要約（2行以内）
2. オーナーの判断・対応が必要な事項（箇条書き）
3. 秘書からの所感・推奨アクション（1行）

【社員Aの日報】
{daily_report}
"""

# 3. Ollama APIの呼び出し
res = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
)
summary = res.json()["response"]

# 4. Inboxフォルダへ出力
with open(INBOX_FILE, "w", encoding="utf-8") as f:
    f.write(f"# 秘書サマリー報告\n日付: 2026-09-26\n\n{summary}")

print("秘書による報告ノートが Inbox に作成されました。")