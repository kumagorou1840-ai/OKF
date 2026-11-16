import os
import json
import subprocess
import urllib.request
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

def strip_think(text: str) -> str:
    if "</think>" in text:
        text = text.split("</think>")[-1]
    return text.replace("```text", "").replace("```", "").strip()

def evaluate_with_jev(reply_text: str) -> dict:
    """jev_eval_tenant.py を使って監査"""
    eval_script = os.path.join(os.path.dirname(__file__), "jev_eval_tenant.py")
    proc = subprocess.run(
        ["python", eval_script],
        input=reply_text,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return json.loads(proc.stdout)

def save_triage_report(tenant_issue: str, reply_text: str, verdict: str, attempts: int, score: float, feedback: str) -> str:
    """Obsidian 06_Reports へレポート保存"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    file_path = os.path.join(REPORTS_DIR, f"Triage_Audit_{timestamp}.md")

    md_content = f"""---
title: "Triage & Audit Report {timestamp}"
date: {date_str}
type: eval_report
category: mail_triage_concierge
status: {verdict}
attempts: {attempts}
score: {score}
model: {MODEL_NAME}
tags:
  - tenant/mail_triage
  - audit/jev
---

# 着信メール トリアージ＆Jev監査レポート

## 概要
- **受付日時**: {date_str}
- **監査判定**: `{verdict}` (Score: {score})
- **修正試行**: {attempts} 回

## 入居者問い合わせ内容
> {tenant_issue}

## Jev 最終監査所見
> {feedback}

## 採用された最終返信案（下書き用）
```text
{reply_text}
```
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n[Obsidian連携] トリアージ監査レポートを保存しました: {file_path}")
    return file_path

def generate_audited_reply(tenant_issue: str, initial_draft: str = "") -> str:
    """入居者からの着信メールに対し、Jev監査・自己改善ループを経た返信案を生成してObsidianに保存する"""
    max_retries = 3
    current_reply = initial_draft or "ご連絡ありがとうございます。水漏れの件、修理代は全額こちらで負担しますので安心してください。明日業者を行かせて確実に直します。"

    score = 0.0
    feedback = ""

    print("=== [開始] 着信メール トリアージ × Jev 監査コネクタ ===")
    print(f"【着信メール内容】: {tenant_issue}")

    for attempt in range(1, max_retries + 1):
        print(f"\n--- [試行 {attempt}/{max_retries}] 返信下書きのJev監査 ---")
        print("【現在の返信案】:\n" + current_reply)

        eval_result = evaluate_with_jev(current_reply)
        verdict = eval_result.get("verdict", "FAIL")
        score = eval_result.get("score", 0.0)
        feedback = eval_result.get("feedback", "")

        print(f"【Jev判定】: {verdict} (Score: {score})")
        print(f"【監査所見】: {feedback}")

        if verdict == "PASS":
            print(f"\n=> 監査合格: 試行 {attempt} 回目で下書きが確定しました！")
            save_triage_report(tenant_issue, current_reply, "PASS", attempt, score, feedback)
            return current_reply

        print("\n=> 不合格のため、Jev監査所見に基づき返信下書きを再生成します...")
        fix_prompt = f"""あなたは賃貸管理会社の優秀なコンシェルジュです。
以下の入居者からの着信メールに対する「元の返信案」には問題があります。
Jev監査エンジンの指摘内容をすべて反映し、入居者へ送る修正後の返信メッセージ本文のみを出力してください。
余計な解説やMarkdownコードブロック（```）は含めないでください。

【入居者からの着信メール】
{tenant_issue}

【元の返信案】
{current_reply}

【Jevの監査指摘（必ずすべて反映すること）】
{feedback}
"""
        current_reply = strip_think(call_ollama(fix_prompt))

    print("\n=> 上限回数に達しましたが合格基準に届きませんでした（要人間確認）。")
    save_triage_report(tenant_issue, current_reply, "FAIL", max_retries, score, feedback)
    return current_reply

# 後方互換エイリアス
process_incoming_tenant_mail = generate_audited_reply

if __name__ == "__main__":
    sample_issue = "【至急・修繕相談】203号室の佐藤です。先ほどからキッチンのシンク下の配管から水がポタポタ漏れて床が濡れています。すぐに対応してもらえますか？"
    generate_audited_reply(
        sample_issue,
        initial_draft="ご連絡ありがとうございます。水漏れの件、修理代は全額こちらで負担しますので安心してください。明日業者を行かせて確実に直します。"
    )
