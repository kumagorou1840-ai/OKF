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


def evaluate_with_noise_jev(reply_text: str) -> dict:
    eval_script = os.path.join(os.path.dirname(__file__), "jev_eval_noise.py")
    proc = subprocess.run(
        ["python", eval_script],
        input=reply_text,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return json.loads(proc.stdout)


def save_noise_report(tenant_issue: str, reply_text: str, verdict: str, attempts: int, score: float, feedback: str):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    file_path = os.path.join(REPORTS_DIR, f"Noise_Triage_Report_{timestamp}.md")

    md_content = f"""---
title: "Noise Triage Evaluation Report {timestamp}"
date: {date_str}
type: eval_report
category: noise_triage
status: {verdict}
attempts: {attempts}
score: {score}
model: {MODEL_NAME}
tags:
  - tenant/noise_triage
  - audit/jev
---

# 騒音・生活マナー苦情対応 Jev監査レポート

## 概要
- **受付日時**: {date_str}
- **監査判定**: `{verdict}` (Score: {score})
- **修正試行**: {attempts} 回

## 入居者問い合わせ内容
> {tenant_issue}

## Jev 最終監査所見
> {feedback}

## 採用された中立返信案
```text
{reply_text}
```
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"\n[Obsidian連携] 騒音苦情監査レポートを保存しました: {file_path}")


def run_noise_test():
    tenant_issue = (
        "302号室の鈴木です。隣の303号室から毎晩深夜1時頃にドンドンという足音や"
        "重低音が響いてきて眠れません。今すぐ303号室の住人に厳重注意して退去させてください！"
    )
    # 初回はわざと一方的な加害者断定＋直接交渉推奨＋退去確約のNGドラフトを入力
    current_reply = (
        "303号室がうるさいのですね。マナー違反ですので、まずはご自身で隣の部屋に直接文句を言ってみてください。"
        "それでも直らなければ、管理会社からすぐに退去させますので安心してください。"
    )

    print("=== [開始] 騒音・生活マナー苦情対応 Jev 監査ループ ===")
    print(f"【入居者相談内容】: {tenant_issue}")

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        print(f"\n--- [試行 {attempt}/{max_retries}] 返信案のJev監査 ---")
        print(f"【現在の返信案】:\n{current_reply}")

        eval_res = evaluate_with_noise_jev(current_reply)
        verdict = eval_res.get("verdict", "FAIL")
        score = eval_res.get("score", 0.0)
        feedback = eval_res.get("feedback", "")

        print(f"【Jev判定】: {verdict} (Score: {score})")
        print(f"【監査所見】: {feedback}")

        if verdict == "PASS":
            print(f"\n=> 監査合格: 試行 {attempt} 回目で中立かつ安全な返信案が確定しました！")
            save_noise_report(tenant_issue, current_reply, verdict, attempt, score, feedback)
            break

        if attempt < max_retries:
            print("\n=> [自己修復] Jevの中立性・トラブル抑止指摘に基づき返信案を再生成します...")
            fix_prompt = f"""あなたは賃貸管理会社のベテランコンシェルジュです。
以下の入居者からの騒音苦情に対する返信文を、監査エンジン（Jev）の指摘に従って完全に修正してください。

【入居者からの相談】
{tenant_issue}

【前回の返信案（不合格）】
{current_reply}

【Jevからの改善指示】
{feedback}

【必須盛り込み事項】
1. 深夜の騒音による睡眠不足やご不快な心情への真摯な共感・お見舞い。
2. 中立性の維持と【Positive Framing（味方としての証拠固め説明）】：建物の構造上、音が上下や斜め方向の別のお部屋から伝わる可能性もあるため特定のお部屋を決めつけずに確認するが、それは「申告者様を疑っているのではなく、今後管理会社から実効性のある強い措置（個別注意や契約上の警告）をとる際に相手方が言い逃れできない『確実な客観的証拠（外堀）』を固めるためである」と味方としての理由を明確に説明すること。
3. 直接トラブルの抑止（Do Now）：ご自身で相手のお部屋へ直接注意・交渉することは思わぬトラブルにつながるため絶対にお控えいただくようお願いすること。
4. 段階的対応の提示：まずは申告者様が特定されない配慮のもと、全戸または該当フロア全体への「夜間生活音に関する注意喚起文の投函（ポスティング）」および「共用掲示板での周知」を速やかに実施する旨を案内すること。
5. 緊急・事件性のある場合の110番案内：万が一、激しい怒鳴り声・暴行音・物の破損音など事件性や身の危険を感じる緊急時は、管理会社の返信を待たず直ちに警察（110番）へ通報いただくよう案内すること。
6. 過度な確約の排除：「すぐに退去させます」「必ず静かにさせます」等の安易・越権的な約束はせず、客観的記録に基づき粘り強く段階的に対応する旨を伝えること。
7. 【末尾の返信フォーマット（Exit Ticket）】：メール末尾に、入居者がそのままコピー＆ペーストして返せる以下の3項目確認フォーマットを明記すること：
   ---
   【ご返信いただきたい3項目（コピーしてご記入ください）】
   ① 発生日時・時間帯と継続時間：
   ② 音が響く物理的方向（北側の壁・天井・床など）と音の種類（足音・重低音・声など）：
   ③ 事件性・緊急性の有無（※激しい怒鳴り声・暴行音等がある場合は直ちに110番へ通報してください）：
   ---

※返信メッセージ本文のみを出力してください（解説や```は不要）。
"""
            current_reply = strip_think(call_ollama(fix_prompt))
    else:
        print("\n=> 最大試行回数に達しました。最終状態をレポート保存します。")
        save_noise_report(tenant_issue, current_reply, verdict, max_retries, score, feedback)

    # ダッシュボードの自動更新
    try:
        from Jev_Audit_Dashboard import build_dashboard
        build_dashboard()
    except ImportError:
        pass


if __name__ == "__main__":
    run_noise_test()
