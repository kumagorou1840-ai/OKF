import os
import imaplib
import email
from email.header import decode_header
from pathlib import Path
from dotenv import load_dotenv

# obsidian_2 直下の .env を読み込む（2階層上を参照）
vault_root = Path(__file__).resolve().parents[2]
load_dotenv(vault_root / ".env")

GMAIL_USER = os.getenv("GMAIL_USER", "your_email@gmail.com")
GMAIL_APP_PASS = (
    os.getenv("GMAIL_APP_PASSWORD")
    or os.getenv("GMAIL_APP_PASS", "your_16_digit_app_password")
).replace(" ", "")

def decode_str(header_value: str) -> str:
    """メールヘッダーの文字化けを解消してデコード"""
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


def fetch_unread_emails(max_count: int = 10) -> list[dict]:
    # GmailのIMAPサーバーへ接続
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(GMAIL_USER, GMAIL_APP_PASS)
    mail.select("INBOX")

    # 未読メールを検索 (UNSEEN)
    status, messages = mail.search(None, "UNSEEN")
    if status != "OK" or not messages[0]:
        mail.logout()
        return []

    mail_ids = messages[0].split()
    target_ids = mail_ids[-max_count:]  # 最新の未読を取得
    target_ids.reverse()

    triage_items = []

    for m_id in target_ids:
        res, msg_data = mail.fetch(m_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_str(msg.get("Subject", "(無題)"))
                sender = decode_str(msg.get("From", "不明"))

                # 簡易判定
                if any(
                    k in subject
                    for k in ["至急", "重要", "確認依頼", "修繕", "契約"]
                ):
                    priority = "🔥 高"
                    action = "至急対応・返信が必要"
                    action_required = True
                elif any(
                    k in sender.lower()
                    for k in ["no-reply", "noreply", "newsletter", "magazine"]
                ):
                    priority = "低"
                    action = "通知/メルマガ（スキップ可）"
                    action_required = False
                else:
                    priority = "中"
                    action = "要確認"
                    action_required = True

                triage_items.append(
                    {
                        "priority": priority,
                        "sender": sender.split("<")[0].strip() or sender,
                        "subject": subject,
                        "action": action,
                        "action_required": action_required,
                    }
                )

    mail.logout()
    return triage_items


def write_to_obsidian(triage_items: list[dict], script_dir: Path):
    vault_root = script_dir.parents[1]
    output_file = vault_root / "00_Inbox" / "Email_Triage.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = [
        "---",
        f"updated: {now_str}",
        "type: email_triage",
        "tags:",
        "  - mail/triage",
        "---",
        "",
        f"# 📨 Email Triage ({now_str})",
        "",
    ]

    if not triage_items:
        content.append("現在、未読のメールはありません。")
    else:
        content.extend(
            [
                "| 重要度 | 送信者 | 件名 | アクション / 要約 |",
                "| :--- | :--- | :--- | :--- |",
            ]
        )
        for item in triage_items:
            # マークダウンのテーブル崩れ防止用サニタイズ
            clean_subject = item["subject"].replace("|", "/")
            clean_sender = item["sender"].replace("|", "/")
            content.append(
                f"| {item['priority']} | {clean_sender} | {clean_subject} | {item['action']} |"
            )

        content.append("\n## 📋 Next Actions")
        for item in triage_items:
            if item["action_required"]:
                clean_sender = item["sender"].replace("[", "").replace("]", "")
                content.append(
                    f"- [ ] **[{clean_sender}]** {item['subject']} ({item['action']})"
                )

    output_file.write_text("\n".join(content), encoding="utf-8")
    print(f"Obsidianノートを更新しました: {output_file}")


def main():
    script_dir = Path(__file__).resolve().parent
    items = fetch_unread_emails()
    write_to_obsidian(items, script_dir)


if __name__ == "__main__":
    main()