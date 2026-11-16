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
    with urllib.request.urlopen(req, timeout=90) as res:
        data = json.loads(res.read().decode("utf-8"))
        return data.get("response", "").strip()

def evaluate_with_jev(reply_text: str) -> dict:
    proc = subprocess.run(
        ["python", "jev_eval.py"],
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


