import os
import sys
import subprocess
import json
import urllib.request
import imaplib
import email
from email.message import EmailMessage
from email.header import decode_header
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from jev_hybrid_auditor import run_hybrid_jev_audit

# --- [1] パス・環境変数設定 ---
script_dir = Path(__file__).resolve().parent
vault_root = script_dir.parent if (script_dir.parent / ".env").exists() else script_dir.parents[1]
demo_dir = script_dir if script_dir.name == "antigravity-Jev-demo" else (vault_root / "antigravity-Jev-demo")
reports_dir = vault_root / "06_Reports"

load_dotenv(vault_root / ".env")

GMAIL_USER = os.getenv("GMAIL_USER", "kumagorou1840@gmail.com")
GMAIL_APP_PASS = (
    os.getenv("GMAIL_APP_PASSWORD")
    or os.getenv("GMAIL_APP_PASS", "")
).replace(" ", "")

MODEL_NAME = "ornith-9b:latest"

# 判別キーワード定義
WINTER_KEYWORDS = ["凍結", "お湯が出ない", "水が出ない", "給湯器", "111", "水抜き", "解氷", "凍っ"]
NOISE_KEYWORDS = ["騒音", "足音", "物音", "うるさい", "声", "重低音", "苦情", "迷惑", "夜中", "マナー"]
REPAIR_KEYWORDS = ["水漏れ", "漏水", "配管", "シンク", "蛇口", "トイレ", "エアコン", "鍵", "故障", "壊れ", "修繕", "至急"]
ALL_TENANT_KEYWORDS = WINTER_KEYWORDS + NOISE_KEYWORDS + REPAIR_KEYWORDS

SKIP_SUBJECT_KEYWORDS = ["【定期配信】", "【日次", "ニュース", "メルマガ", "Information", "オープンベータ", "Weekend vol"]


# --- [2] Ollama / Jev 評価ヘルパー ---
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


def run_jev_evaluator(eval_script_name: str, draft_text: str) -> dict:
    """指定された Jev 監査エンジン（子プロセス）を実行"""
    script_path = demo_dir / eval_script_name
    proc = subprocess.run(
        ["python", str(script_path)],
        input=draft_text,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return json.loads(proc.stdout)


def route_inquiry(subject: str, body: str) -> tuple[str, str, str]:
    """
    着信メールの件名・本文から最適なJev監査器とカテゴリを自動判定
    戻り値: (category, eval_script, system_role_prompt)
    """
    text = f"{subject}\n{body}"
    
    # 1. 冬期凍結・給湯器判定
    if any(k in text for k in WINTER_KEYWORDS):
        return (
            "winter_freeze_triage",
            "jev_eval_winter.py",
            """あなたは北海道の寒冷地賃貸管理に精通した管理人です。
- 熱湯を直接かけると急激な温度差で配管が破裂するため絶対に禁止し、ぬるま湯（タオルを巻く）、ドライヤーの温風、室内暖房での自然解凍を指示すること。
- 給湯器エラー111について、屋外の給排気筒（煙突トップ）が雪や氷柱で埋まっていないか安全な目視確認を依頼すること。
- 費用については原因（経年劣化か過失・水抜き不足か）を確認の上での協議とし、事前全額負担を確約しないこと。"""
        )

    # 2. 騒音・生活マナー苦情判定
    if any(k in text for k in NOISE_KEYWORDS):
        return (
            "noise_triage",
            "jev_eval_noise.py",
            """あなたは賃貸住宅の公平で冷静な管理人です。
- 申告者の不快感やつらさには共感しつつ、調査前のため相手方を一方的に加害者と断定しないこと。
- 入居者同士の直接対決は重大な二次トラブルを招くため絶対に禁止し、管理側へ任せるよう伝えること。
- 「発生日時・音の種類・頻度」の客観的記録（メモ）を依頼すること。
- 名指しではなく、まずは該当フロア全体への「注意喚起文の配布・掲示」から段階的に対応する方針を提示すること。"""
        )

    # 3. 一般設備修繕・水漏れ判定（デフォルト）
    return (
        "mail_triage_concierge",
        "jev_eval_tenant.py",
        """あなたは賃貸住宅の丁寧な管理人です。
- 入居者の不安に寄り添い丁寧に対応すること。
- 止水栓の確認や写真撮影の依頼など、被害拡大を防ぐ一時対応を指示すること。
- 現地未確認の段階で「全額負担」「明日確実に直る」等の安易な確約を避け、原因確認後の協議とすること。
- 状況確認のための訪問候補日を提示すること。"""
    )


def determine_lane(verdict: str, domain_score: float, reply_text: str) -> tuple[str, str]:
    """ドメインJev監査スコアと3層ハイブリッド監査を組み合わせ、3レーンと件名タグを決定"""
    hybrid_rep = run_hybrid_jev_audit(reply_text, fast_fail=False)
    if verdict == "PASS" and domain_score >= 0.90 and hybrid_rep.action_lane == "AUTO_APPROVE":
        return "AUTO_APPROVE", "[✅Jev自動承認済]"
    if verdict == "PASS" and hybrid_rep.action_lane != "AUTO_REJECT":
        return "HUMAN_REVIEW", "[⚠️要よっちゃん確認]"
    if verdict == "PASS":
        return "HUMAN_REVIEW", "[⚠️要よっちゃん確認]"
    return "AUTO_REJECT", "[🛑送信不可・自動差戻し]"


def generate_audited_reply_routed(tenant_issue: str, max_retries: int = 3) -> tuple[str, str, str, str, str]:
    """着信内容をルーティング判定し、早期打ち切り(Fast-Fail)＋Jev監査・自己修復ループを実行"""
    category, eval_script, role_prompt = route_inquiry("", tenant_issue)
    print(f"  => [自動ルーティング] カテゴリ: `{category}` | 監査器: `{eval_script}`")

    # 初回ドラフト生成
    draft_prompt = f"""あなたは賃貸住宅の管理人です。以下の入居者からの問い合わせに対して、返信案を作成してください。
思考プロセスや前置きは含めず、返信文のみを出力してください。

【入居者の問い合わせ】
{tenant_issue}
"""
    raw_draft = call_ollama(draft_prompt)
    if "</think>" in raw_draft:
        raw_draft = raw_draft.split("</think>")[-1]
    current_reply = raw_draft.strip().replace("```text", "").replace("```", "")

    score = 0.0
    feedback = ""

    # Jev 監査・自己修復ループ（第1層 Fast-Fail ゲート ＋ 専門ドメイン Jev）
    for attempt in range(1, max_retries + 1):
        # 1. 第1層（二値ゲート）による高速早期打ち切りチェック
        pre_check = run_hybrid_jev_audit(current_reply, fast_fail=True)
        if pre_check.fast_failed:
            score = pre_check.total_score
            feedback = pre_check.summary_feedback
            print(f"    => ⚡ [Fast-Fail 早期打ち切り] 試行 {attempt}/{max_retries}: {pre_check.bool_audit['reason']}")
        else:
            # 2. 専門ドメイン Jev 監査の実行
            print(f"    [Jev監査] 試行 {attempt}/{max_retries} ({eval_script}) 実行中...")
            eval_result = run_jev_evaluator(eval_script, current_reply)
            verdict = eval_result.get("verdict")
            score = eval_result.get("score", 0.0)
            feedback = eval_result.get("feedback", "")

            if verdict == "PASS":
                action_lane, draft_prefix = determine_lane("PASS", score, current_reply)
                print(f"    => ✅ PASS 合格 (Score: {score} / Lane: {action_lane} {draft_prefix})")
                save_audit_report(tenant_issue, current_reply, category, "PASS", attempt, score, feedback, action_lane, draft_prefix)
                return current_reply, category, "PASS", action_lane, draft_prefix

            print(f"    => ❌ FAIL 指摘 (Score: {score}): {feedback}")

        fix_prompt = f"""{role_prompt}

監査役（Jev）からの指摘をすべて反映し、リスクを排除した修正返信文を作成してください。
思考プロセスや前置きは含めず、返信文面のみを出力してください。

【入居者の問い合わせ】
{tenant_issue}

【不十分な返信】
{current_reply}

【Jev監査の指摘】
{feedback}
"""
        raw_fix = call_ollama(fix_prompt)
        if "</think>" in raw_fix:
            raw_fix = raw_fix.split("</think>")[-1]
        current_reply = raw_fix.strip().replace("```text", "").replace("```", "")

    action_lane, draft_prefix = determine_lane("FAIL", score, current_reply)
    save_audit_report(tenant_issue, current_reply, category, "FAIL", max_retries, score, feedback, action_lane, draft_prefix)
    return current_reply, category, "FAIL", action_lane, draft_prefix


def save_audit_report(
    tenant_issue: str,
    reply_text: str,
    category: str,
    verdict: str,
    attempts: int,
    score: float,
    feedback: str,
    action_lane: str = "AUTO_APPROVE",
    draft_prefix: str = "[✅Jev自動承認済]",
):
    """06_Reports へ Markdown レポート保存"""
    reports_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    file_path = reports_dir / f"Audit_{category}_{timestamp}.md"

    md_content = f"""---
title: "Audit Report {category} {timestamp}"
date: {date_str}
type: eval_report
category: {category}
status: {verdict}
action_lane: {action_lane}
draft_prefix: "{draft_prefix}"
attempts: {attempts}
score: {score}
model: {MODEL_NAME}
tags:
  - tenant/{category}
  - audit/jev
---

# Jev 監査・自動トリアージレポート

## 概要
- **受付日時**: {date_str}
- **判定カテゴリ**: `{category}`
- **監査判定**: `{verdict}` (Score: {score})
- **仕分けレーン**: `{action_lane}` (`{draft_prefix}`)
- **修正試行**: {attempts} 回

## 入居者問い合わせ内容
> {tenant_issue}

## Jev 最終監査所見
> {feedback}

## 採用された確定返信案
```text
{reply_text}
```
"""
    file_path.write_text(md_content, encoding="utf-8")
    print(f"    => [Obsidian連携] レポート保存完了: {file_path}")


# --- [3] メール受信・下書き保存ヘルパー ---
def decode_str(header_value: str) -> str:
    if not header_value:
        return ""
    decoded_fragments = decode_header(header_value)
    result = []
    for text, encoding in decoded_fragments:
        if isinstance(text, bytes):
            result.append(text.decode(encoding or "utf-8", errors="ignore"))
        else:
            result.append(str(text))
    return "".join(result)


def extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="ignore")
    else:
        payload = msg.get_payload(decode=True)
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="ignore")
    return ""


def save_to_gmail_drafts(to_email: str, subject: str, reply_body: str, draft_prefix: str = ""):
    """IMAP APPEND を使い、Jev監査済みの文面を3レーン件名タグ付きで Gmail の「下書き」フォルダに自動保存"""
    try:
        msg = EmailMessage()
        msg["From"] = GMAIL_USER
        msg["To"] = to_email
        base_subj = f"Re: {subject}" if not subject.startswith("Re:") else subject
        msg["Subject"] = f"{draft_prefix} {base_subj}".strip() if draft_prefix else base_subj
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg.set_content(reply_body)

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASS)

        draft_box = '"[Gmail]/&Tgtm+DBN-"'
        _, boxes = mail.list()
        for b in boxes or []:
            line = b.decode("utf-8", errors="ignore")
            if "\\Drafts" in line and '"' in line:
                draft_box = '"' + line.split('"')[-2] + '"'
                break
        mail.select(draft_box)

        mail.append(draft_box, "\\Draft", imaplib.Time2Internaldate(datetime.now().astimezone()), msg.as_bytes())
        mail.logout()
        print(f"  => [Gmail下書き完了] {draft_box} に下書きを保存しました。")
    except Exception as e:
        print(f"  => [Gmail下書きエラー] 保存に失敗しました: {e}")


# --- [4] メインパイプライン処理 ---
def run_triage_and_audit_pipeline():
    print("=== [Mail Triage Bot] Gmail 受信 & 3系統 Jev マルチ監査パイプライン開始 ===")

    if not GMAIL_APP_PASS:
        print("エラー: .env に GMAIL_APP_PASSWORD が設定されていません。")
        return

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASS)
        mail.select("INBOX")
    except Exception as e:
        print(f"Gmail接続エラー: {e}")
        return

    status, messages = mail.search(None, "UNSEEN")
    if status != "OK" or not messages[0]:
        print("現在、未読のメールはありません。")
        mail.logout()
        return

    mail_ids = messages[0].split()
    target_ids = mail_ids[-5:]
    target_ids.reverse()

    for m_id in target_ids:
        res, msg_data = mail.fetch(m_id, "(RFC822)")
        for response_part in msg_data:
            if not isinstance(response_part, tuple):
                continue

            msg = email.message_from_bytes(response_part[1])
            subject = decode_str(msg.get("Subject", "(無題)"))
            sender = decode_str(msg.get("From", "不明"))
            body_text = extract_body(msg).strip()

            print(f"\n--------------------------------------------------")
            print(f"【受信】送信者: {sender} | 件名: {subject}")

            if any(k in sender.lower() for k in ["no-reply", "noreply", "newsletter", "magazine"]) or any(
                sk in subject for sk in SKIP_SUBJECT_KEYWORDS
            ):
                print("  => [スキップ] メルマガ・定期配信ニュースのため対応不要")
                continue

            short_body = body_text[:800]

            if any(k in subject or k in short_body for k in ALL_TENANT_KEYWORDS):
                print("  => [🔥 入居者相談・トラブル案件を検知]")
                inquiry_content = f"件名: {subject}\n差出人: {sender}\n本文: {short_body}"

                audited_reply, category, verdict, action_lane, draft_prefix = generate_audited_reply_routed(inquiry_content)

                print(f"\n  === [Jev確定返信文面 ({category} / {verdict} / {action_lane})] ===")
                print(audited_reply)

                from_email = email.utils.parseaddr(sender)[1] or sender
                save_to_gmail_drafts(
                    to_email=from_email,
                    subject=subject,
                    reply_body=audited_reply,
                    draft_prefix=draft_prefix,
                )
            else:
                print("  => [通常案件] 入居者トラブル・修繕以外のメールです。")

    mail.logout()
    print("\n=== [完了] すべての未読メールの処理が終了しました ===")


if __name__ == "__main__":
    run_triage_and_audit_pipeline()

    try:
        from Jev_Audit_Dashboard import build_dashboard
        build_dashboard()
        print("\n[連携完了] Jev_Audit_Dashboard.md を最新状態に自動更新しました。")
    except ImportError:
        pass
