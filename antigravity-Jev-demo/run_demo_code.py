import subprocess
import json
import urllib.request
import os
from datetime import datetime

MODEL_NAME = "ornith-9b:latest"

# Obsidian_2 内の出力先フォルダ（親フォルダの 06_Reports を指定）
REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "06_Reports"))

def call_ollama(prompt: str) -> str:
    """Ollamaにプロンプトを送り、テキストを生成するヘルパー"""
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

def evaluate_with_jev(code: str) -> dict:
    """Jev評価スクリプトを子プロセスとして呼び出す"""
    proc = subprocess.run(
        ["python", "jev_eval_code.py"],
        input=code,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return json.loads(proc.stdout)

def save_report_to_obsidian(status: str, attempts: int, score: float, feedback: str, code: str):
    """評価結果をObsidian用Markdownレポートとして保存"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    now = datetime.now()
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    file_path = os.path.join(REPORTS_DIR, f"Jev_Report_{timestamp_str}.md")

    md_content = f"""---
title: "Jev Evaluation Report {timestamp_str}"
date: {date_str}
type: eval_report
status: {status}
attempts: {attempts}
score: {score}
model: {MODEL_NAME}
tags:
  - evaluation/jev
  - log/antigravity
---

# Jev 評価実行レポート

## 概要
- **実行日時**: {date_str}
- **最終判定**: `{status}`
- **試行回数**: {attempts} 回
- **最終スコア**: {score}

## Jev フィードバック
> {feedback}

## 最終成果物コード
```python
{code}
```
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n[Obsidian連携] レポートを保存しました: {file_path}")

def run_self_healing_pipeline():
    max_retries = 3
    # 初期入力（わざと構文エラーを含めたコード）
    current_code = "def calc_total(price, tax):\n    return price * (1 + tax"
    score = 0.0
    feedback = ""

    print("=== [開始] Antigravity × Jev 自己改善ループ ===")
    
    for attempt in range(1, max_retries + 1):
        print(f"\n--- [試行 {attempt}/{max_retries}] コード検証 ---")
        print("【対象コード】:\n" + current_code)

        # 1. Jevによる評価
        eval_result = evaluate_with_jev(current_code)
        verdict = eval_result.get("verdict")
        score = eval_result.get("score", 0.0)
        feedback = eval_result.get("feedback", "")

        print(f"【Jev判定】: {verdict} (Score: {score})")
        print(f"【指摘内容】: {feedback}")

        # 合格判定
        if verdict == "PASS":
            print(f"\n=> 成功: 試行 {attempt} 回目で合格基準をクリアしました！")
            save_report_to_obsidian("PASS", attempt, score, feedback, current_code)
            return

        # 不合格時の自動修復（フィードバックを元にLLMへ修正を要求）
        print("\n=> 判定が不合格のため、Jevの指摘をもとにコードを自動修復します...")
        fix_prompt = f"""以下のコードには欠陥があります。Jevの指摘内容を忠実に反映し、修正後の完全なPythonコードのみを出力してください。
Markdownのコードブロック（```python ... ```）や余計な解説文は含めず、純粋なコードのみを出力してください。

【元のコード】
{current_code}

【Jevの指摘内容】
{feedback}
"""
        raw_fix = call_ollama(fix_prompt)
        # 推論タグ（思考ログ）の除去
        if "</think>" in raw_fix:
            raw_fix = raw_fix.split("</think>")[-1]
            
        current_code = raw_fix.replace("```python", "").replace("```", "").strip()

    print("\n=> 上限回数に達しましたが合格できませんでした。")
    save_report_to_obsidian("FAIL", max_retries, score, feedback, current_code)

if __name__ == "__main__":
    run_self_healing_pipeline()
