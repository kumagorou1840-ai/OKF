import requests
import json
import os
import re
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "ornith-9b:latest"

BASE_DIR = r"C:\Users\PC_User\Documents\Obsidian\obsidian_1\AI_Office"
DISCUSSION_DIR = os.path.join(BASE_DIR, "Discussion_Room")
INBOX_DIR = os.path.join(BASE_DIR, "Inbox_Office")

def clean_text(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    text = re.sub(r".*</think>", "", text, flags=re.DOTALL)
    lines = text.strip().split("\n")
    japanese_lines = []
    for line in lines:
        line_clean = line.strip().strip('"').strip("'")
        if re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", line_clean):
            japanese_lines.append(line_clean)
    return "\n".join(japanese_lines).strip()

def summarize_discussion():
    today_str = datetime.now().strftime("%Y-%m-%d")
    disc_file = os.path.join(DISCUSSION_DIR, f"{today_str}_Discussion_Log.md")
    
    if not os.path.exists(disc_file):
        print(f"議論ログが見つかりません: {disc_file}")
        return

    with open(disc_file, "r", encoding="utf-8-sig") as f:
        log_content = f.read()

    prompt = f"""あなたは優秀な秘書AIです。
以下の「AI社員たちの会議ログ」を読み、オーナー（経営判断者）向けに要約してください。

【会議ログ】
{log_content}

以下のフォーマット（Markdown形式）で日本語のみで出力してください。挨拶や思考ログは不要です。

## 社員会議サマリー
- 各社員の対立点と合意事項の要点（2〜3行）

## 秘書としての最終推奨案
- オーナーが意思決定すべき方向性の提案（1〜2行）
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": "あなたは優秀な秘書です。思考過程や英語は出力せず、Markdown形式の日本語のみを出力してください。",
        "stream": False,
        "options": {"temperature": 0.3}
    }

    print("秘書AIが議論ログを分析中...")
    res = requests.post(OLLAMA_URL, json=payload)
    summary_text = clean_text(res.json().get("response", ""))

    output_path = os.path.join(INBOX_DIR, f"{today_str}_Secretary_Summary.md")
    with open(output_path, "a", encoding="utf-8-sig") as f:
        f.write(f"\n\n---\n\n{summary_text}\n")

    print(f"秘書サマリーを追記しました: {output_path}")

if __name__ == "__main__":
    summarize_discussion()