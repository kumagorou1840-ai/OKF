import os
import sys
import json
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

MODEL_NAME = "ornith-9b:latest"
VAULT_ROOT = Path(__file__).resolve().parent.parent
LINKS_DIR = VAULT_ROOT / "03_Resources" / "Links"

def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=90) as res:
        data = json.loads(res.read().decode("utf-8"))
        return data.get("response", "").strip()

def evaluate_with_jev(triage_json_str: str) -> dict:
    eval_script = Path(__file__).resolve().parent / "jev_eval_link.py"
    proc = subprocess.run(
        ["python", str(eval_script)],
        input=triage_json_str,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return json.loads(proc.stdout)

def classify_link(url: str, title: str, snippet: str = ""):
    print(f"=== [Link Triage] 分類開始: {title} ===")
    
    link_info = f"URL: {url}\nタイトル: {title}\n概要/メモ: {snippet}"
    current_prompt = f"""以下のWebリンク情報を読み取り、適切なカテゴリ・タグ・分類根拠をJSON形式で出力してください。

【許容メインカテゴリ】
`real_estate`, `tech_ai`, `math_science`, `economy_geopolitics`, `general_reading`

【リンク情報】
{link_info}

【出力JSON形式】
{{
  "category": "カテゴリ名",
  "tags": ["tag1", "tag2"],
  "summary": "1行概要",
  "justification": "このカテゴリに分類した客観的根拠"
}}
"""
    max_retries = 3
    current_json = call_ollama(current_prompt)

    for attempt in range(1, max_retries + 1):
        print(f"--- [試行 {attempt}/{max_retries}] Jev 監査中 ---")
        eval_result = evaluate_with_jev(current_json)
        verdict = eval_result.get("verdict")
        score = eval_result.get("score", 0.0)
        feedback = eval_result.get("feedback", "")

        print(f"  Jev判定: {verdict} (Score: {score})")
        if verdict == "PASS":
            print(f"  => 承認完了: 精度基準をクリアしました。")
            save_link_note(url, title, json.loads(current_json))
            return

        print(f"  => 指摘: {feedback}")
        fix_prompt = f"""前回の分類結果がJev監査で不合格となりました。
以下の指摘内容を完全に反映し、正しいJSON形式で再出力してください。

【リンク情報】
{link_info}

【前回の不十分な結果】
{current_json}

【Jev監査の指摘】
{feedback}
"""
        current_json = call_ollama(fix_prompt)

    print("=> 規定回数内にPASS基準に達しませんでした（保留として保存）。")

def save_link_note(url: str, title: str, meta: dict):
    LINKS_DIR.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')[:50].strip()
    file_path = LINKS_DIR / f"{safe_title}.md"
    
    tags_str = "\n".join([f"  - {t}" for t in meta.get("tags", [])])
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f"""---
title: "{title}"
url: "{url}"
category: "{meta.get('category')}"
date: {now_str}
tags:
{tags_str}
---

# {title}

- **URL**: [{url}]({url})
- **カテゴリ**: `{meta.get('category')}`
- **概要**: {meta.get('summary')}

## 🏷️ 分類根拠 (Jev Justification)
> {meta.get('justification')}
"""
    file_path.write_text(content, encoding="utf-8")
    print(f"  [Obsidian] リンクノートを作成しました: {file_path.name}")

if __name__ == "__main__":
    # テスト用
    test_url = "https://example.com/hokkaido-real-estate-tax-2026"
    test_title = "【2026年最新】札幌市の賃貸オーナー必見！固定資産税と冬期修繕費用の節税対策まとめ"
    test_snippet = "札幌市内の集合住宅を管理する家主向けに、水道管凍結や除雪費用を修繕費として計上する際の注意点を税理士が解説。"
    classify_link(test_url, test_title, test_snippet)