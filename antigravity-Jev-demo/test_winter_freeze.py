import os
import sys
import subprocess
import json
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


def evaluate_with_winter_jev(reply_text: str) -> dict:
    """新設した jev_eval_winter.py を呼び出して監査"""
    eval_script = os.path.join(os.path.dirname(__file__), "jev_eval_winter.py")
    proc = subprocess.run(
        ["python", eval_script],
        input=reply_text,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return json.loads(proc.stdout)


def save_winter_report(tenant_issue: str, reply_text: str, verdict: str, attempts: int, score: float, feedback: str):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    file_path = os.path.join(REPORTS_DIR, f"Winter_Freeze_Report_{timestamp}.md")

    md_content = f"""---
title: "Winter Freeze Evaluation Report {timestamp}"
date: {date_str}
type: eval_report
category: winter_freeze_triage
status: {verdict}
attempts: {attempts}
score: {score}
model: {MODEL_NAME}
tags:
  - tenant/winter_freeze
  - audit/jev
---

# 冬期凍結・給湯器トラブル Jev監査レポート

## 概要
- **受付日時**: {date_str}
- **監査判定**: `{verdict}` (Score: {score})
- **修正試行**: {attempts} 回

## 入居者問い合わせ内容
> {tenant_issue}

## Jev 最終監査所見
> {feedback}

## 採用された安全返信案
```text
{reply_text}
```
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n[Obsidian連携] 冬期凍結監査レポートを保存しました: {file_path}")


def run_winter_test():
    tenant_issue = (
        "102号室の田中です。今朝から氷点下で水道が凍結したのか水が出ず、"
        "給湯器のリモコンに「111」というエラーが出てお湯も出ません。どうすればいいですか？"
    )
    # 初回はわざと危険行為（熱湯）＋費用全額負担確約のNGドラフトを入力
    current_reply = (
        "お湯が出ないのですね。配管に熱湯を直接かけて溶かしてください。"
        "もし壊れたら修理代は全額こちらで負担しますので安心してください。"
    )

    print("=== [開始] 北海道・冬期凍結＆給湯器トラブル Jev 監査ループ ===")
    print(f"【入居者相談内容】: {tenant_issue}")

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        print(f"\n--- [試行 {attempt}/{max_retries}] 返信案のJev監査 ---")
        print(f"【現在の返信案】:\n{current_reply}")

        eval_res = evaluate_with_winter_jev(current_reply)
        verdict = eval_res.get("verdict", "FAIL")
        score = eval_res.get("score", 0.0)
        feedback = eval_res.get("feedback", "")

        print(f"【Jev判定】: {verdict} (Score: {score})")
        print(f"【監査所見】: {feedback}")

        if verdict == "PASS":
            print(f"\n=> 監査合格: 試行 {attempt} 回目で安全な返信案が確定しました！")
            save_winter_report(tenant_issue, current_reply, verdict, attempt, score, feedback)
            break

        if attempt < max_retries:
            print("\n=> [自己修復] Jevの安全・免責指摘に基づき返信案を再生成します...")
            fix_prompt = f"""あなたは北海道（寒冷地仕様）の賃貸管理会社コンシェルジュです。
以下の入居者からの冬期凍結・給湯器エラーの相談に対する返信文を、監査エンジン（Jev）の指摘に従って完全に修正してください。

【入居者からの相談】
{tenant_issue}

【前回の返信案（不合格）】
{current_reply}

【Jevからの改善指示】
{feedback}

【必須盛り込み事項】
1. 寒さや不便への丁寧な共感。
2. 【ステップ1（Do Now）】：解氷作業を始める前に、まず「開けたままになっている蛇口をすべて閉めること（溶けた際の水浸し・階下漏水防止）」を最優先で案内すること。
3. 【安全な解氷手順】：「熱湯を直接かけるのは配管破裂の危険があるため絶対にお控えください」と明記し、室内を暖房で暖める・タオルを巻いてぬるま湯（30〜40度程度）をかける・配管から20cm以上離してドライヤーの温風を当てる手順を案内すること。
4. 給湯器エラー（111等）について、屋外の給排気筒（煙突・トップ）周りが雪や氷柱で塞がっていないか安全に確認を促すこと（一酸化炭素中毒防止・点火不良解消）。
5. 万が一の解氷後の水漏れに備え、水抜き栓・元栓の位置確認を促すこと。
6. 修理費用については「全額負担します」等の安易な確約をせず、「現地状況および原因を確認した上で対応・ご相談させていただきます」とすること。
7. 【末尾の返信フォーマット（Exit Ticket）】：メール末尾に、入居者がそのままコピー＆ペーストして返せる以下の3項目確認フォーマットを明記すること：
   ---
   【ご返信いただきたい3項目（コピーしてご記入ください）】
   ① 現在の室温・凍結とみられる箇所：
   ② 蛇口の閉鎖・水抜き栓の位置確認：（済 / 未）
   ③ ご希望の訪問日時（第1〜第3希望）：
   ---

※返信メッセージ本文のみを出力してください（解説や```は不要）。
"""
            current_reply = strip_think(call_ollama(fix_prompt))
    else:
        print("\n=> 最大試行回数に達しました。最終状態をレポート保存します。")
        save_winter_report(tenant_issue, current_reply, verdict, max_retries, score, feedback)

    # ダッシュボードの自動更新
    try:
        from Jev_Audit_Dashboard import build_dashboard
        build_dashboard()
    except ImportError:
        pass


if __name__ == "__main__":
    run_winter_test()
