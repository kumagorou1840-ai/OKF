import subprocess
import json
import urllib.request
import os
from datetime import datetime

MODEL_NAME = "ornith-9b:latest"
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "06_Reports"))

def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=300) as res:
        data = json.loads(res.read().decode("utf-8"))
        return data.get("response", "").strip()

def evaluate_with_jev(reply_text: str) -> dict:
    proc = subprocess.run(
        ["python", "jev_eval_tenant.py"],
        input=reply_text,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return json.loads(proc.stdout)

def save_report_to_obsidian(status: str, attempts: int, score: float, feedback: str, reply_text: str):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    now = datetime.now()
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    file_path = os.path.join(REPORTS_DIR, f"Tenant_Reply_Report_{timestamp_str}.md")

    md_content = f"""---
title: "Tenant Reply Evaluation {timestamp_str}"
date: {date_str}
type: eval_report
category: tenant_inquiry
status: {status}
attempts: {attempts}
score: {score}
model: {MODEL_NAME}
tags:
  - evaluation/tenant_concierge
  - property_management
---

# 入居者問い合わせ対応文 評価レポート

## 概要
- **実行日時**: {date_str}
- **最終判定**: `{status}`
- **試行回数**: {attempts} 回
- **評価スコア**: {score}

## Jev 監査フィードバック
> {feedback}

## 最終確定した返信文案
```text
{reply_text}
```
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n[Obsidian連携] レポートを保存しました: {file_path}")

def run_tenant_concierge_pipeline():
    max_retries = 3
    # 初期返信案（わざと雑・リスクのある対応文）
    current_reply = "水漏れですね。修理代は全額こちらで負担しますので安心してください。明日業者を行かせて確実に直します。"
    score = 0.0
    feedback = ""

    print("=== [開始] 入居者問い合わせ返信案 × Jev 監査・自己改善ループ ===")

    for attempt in range(1, max_retries + 1):
        print(f"\n--- [試行 {attempt}/{max_retries}] 返信文案の監査 ---")
        print("【対象返信案】:\n" + current_reply)

        eval_result = evaluate_with_jev(current_reply)
        verdict = eval_result.get("verdict")
        score = eval_result.get("score", 0.0)
        feedback = eval_result.get("feedback", "")

        print(f"【Jev判定】: {verdict} (Score: {score})")
        print(f"【監査指摘】: {feedback}")

        if verdict == "PASS":
            print(f"\n=> 成功: 試行 {attempt} 回目で監査基準をクリアしました！")
            save_report_to_obsidian("PASS", attempt, score, feedback, current_reply)
            return

        print("\n=> 判定が不合格のため、Jevの監査指摘をもとに返信文案を自動推敲します...")
        fix_prompt = f"""あなたは賃貸管理会社の優秀なコンシェルジュです。
以下の「元の返信案」には問題があります。Jev監査エンジンの指摘内容をすべて反映し、入居者へ送る修正後の返信メッセージ本文のみを出力してください。
余計な解説やMarkdownコードブロック（```）は含めないでください。

【入居者からの相談内容】
キッチンのシンク下から水漏れしています。どうすればいいですか？

【元の返信案】
{current_reply}

【Jevの監査指摘（必ずすべて反映すること）】
{feedback}
"""
        raw_fix = call_ollama(fix_prompt)
        if "</think>" in raw_fix:
            raw_fix = raw_fix.split("</think>")[-1]

        current_reply = raw_fix.replace("```text", "").replace("```", "").strip()

    print("\n=> 上限回数に達しましたが合格できませんでした。")
    save_report_to_obsidian("FAIL", max_retries, score, feedback, current_reply)

if __name__ == "__main__":
    run_tenant_concierge_pipeline()
