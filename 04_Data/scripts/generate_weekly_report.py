import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import google.generativeai as genai

# Windowsコンソール（CP932）環境での文字化け・出力エラー対策
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# obsidian_2 ルートパスと .env の読み込み
vault_root = Path(__file__).resolve().parents[2]
load_dotenv(vault_root / ".env")

# APIキーおよびGmail認証情報の取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError(".env ファイルに GEMINI_API_KEY が設定されていません。")

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASS = (
    os.getenv("GMAIL_APP_PASS") or os.getenv("GMAIL_APP_PASSWORD") or ""
).replace(" ", "")

# 配信先リスト（自身のGmail、または届けたいメールアドレス）
DISTRIBUTION_LIST = [GMAIL_USER]

# Gemini API の設定
genai.configure(api_key=GEMINI_API_KEY)

RAW_DIR = vault_root / "04_Data" / "raw" / "daily_news"
REPORT_DIR = vault_root / "06_Reports"


def collect_week_news(days: int = 7) -> str:
    """過去指定日数分のニューステキストを結合して取得"""
    if not RAW_DIR.exists():
        return ""

    today = datetime.now().date()
    collected = []

    # 時系列順（古い日付から新しい日付へ）
    for i in reversed(range(days)):
        target_date = today - timedelta(days=i)
        target_file = RAW_DIR / f"{target_date.strftime('%Y-%m-%d')}.txt"
        if target_file.exists():
            text = target_file.read_text(encoding="utf-8").strip()
            if text:
                collected.append(f"### 日付: {target_date.strftime('%Y-%m-%d')}\n{text}")

    return "\n\n".join(collected)


def send_report_email(subject: str, markdown_content: str):
    """生成されたレポートをGmail SMTPで配信"""
    if not GMAIL_USER or not GMAIL_APP_PASS:
        print("⚠️ メール送信スキップ: .env に GMAIL_USER / GMAIL_APP_PASS が見つかりません。")
        return

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = ", ".join(DISTRIBUTION_LIST)
    msg["Subject"] = Header(subject, "utf-8")

    # 本文（プレーンテキスト）
    msg.attach(MIMEText(markdown_content, "plain", "utf-8"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.send_message(msg)
        server.quit()
        print(f"📧 レポートをメール配信しました: {msg['To']}")
    except Exception as e:
        print(f"❌ メール配信エラー: {e}")


def generate_weekly_report():
    print("📥 過去7日間のニュース素材を収集中...")
    input_text = collect_week_news(days=7)

    if not input_text:
        print("⚠️ 過去7日間のニュースデータ (04_Data/raw/daily_news/) が見つかりませんでした。")
        print("先に mail_triage_bot.py を実行してニュースを蓄積してください。")
        return

    # プロンプトの組み立て
    prompt = f"""あなたは地政学・マクロ経済、および不動産・事業環境のシニアアナリストです。
以下に提供される【過去7日間の日次ニュース・動向テキスト】を横断的に分析し、
定期配信用の「地政学・経済動向ニュースレポート」の骨子と、今後の行方に関する【3つの未来シナリオ】を作成してください。

---

### 出力フォーマット（Markdown形式で直接出力してください）

# 🌐 週次 地政学・マクロ経済レポート

## 1. 今週の大局構図（マクロの気配・潮目）
- 今週起きた複数の事象を貫く「最も大きな構造変化・テーマ」を2〜3行で簡潔に要約。

## 2. 主要トピックの定点観測
### (1) 地政学・国際秩序（米中対立、地域紛争、資源・サプライチェーン動向）
- 事象の要約と、中長期的なパワーバランスへの影響。

### (2) グローバルマクロ・金融政策（金利、インフレ、為替動向）
- 米欧・主要国の金融政策や重要指標の動向。

### (3) 国内経済・不動産実体市場への波及
- 長期金利の動向、建築・修繕資材コスト、入居需要や資金調達への影響。

---

## 3. Gemini推論：今後の行方（3つの未来シナリオ）

直近の動向を踏まえ、今後1〜3ヶ月で想定される展開を以下の3パターンで構造化してください。

### ① パターンA：メインシナリオ（最も蓋然性が高い基調・確率 60%）
- **前提条件・展開**: 現在のトレンドが継続した場合の展開
- **市場・経済の反応**: 金利、為替、物価の着地点
- **事業・不動産への示唆**: 賃料設定、修繕計画、資金調達でとるべき標準アクション

### ② パターンB：ポジティブ / 安定シナリオ（好材料の顕在化・確率 20%）
- **前提条件・展開**: インフレ沈静化、地政学的緊張の緩和、景気回復などのトリガー
- **市場・経済の反応**: コスト安定化、マインド改善
- **事業・不動産への示唆**: 設備投資や新規展開の検討ポイント

### ③ パターンC：リスク / 警戒シナリオ（逆風・下振れリスク・確率 20%）
- **前提条件・展開**: 紛争激化、資源急騰、金利の想定外上昇、市場急変などのトリガー
- **市場・経済の反応**: 急激な為替変動、コスト高騰、需要後退
- **事業・不動産への示唆**: キャッシュ確保、修繕・工事の延期判断、防衛的対応

---

## 4. 来週の注視ポイント・イベント
- [ ] 発表予定の重要指標（米雇用統計、CPI、日銀会合等）
- [ ] 警戒すべき地政学的タイムライン

---

### 【過去7日間の日次ニュース・動向テキスト】
{input_text}
"""

    print("🧠 Gemini モデルで推論・レポート生成中...")
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    # 保存先の設定
    now = datetime.now()
    week_str = now.strftime("%Y_W%W")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = REPORT_DIR / f"Weekly_Outlook_{week_str}.md"

    # Frontmatter の付与
    frontmatter = [
        "---",
        f"updated: {now.strftime('%Y-%m-%d %H:%M')}",
        "type: weekly_outlook",
        "tags:",
        "  - report/weekly",
        "  - macro/geopolitics",
        "  - macro/forecast",
        "---",
        "",
        "",
    ]

    # 1. Obsidianへ保存
    output_file.write_text("\n".join(frontmatter) + response.text, encoding="utf-8")
    print(f"✅ 週次予測レポートを保存しました: {output_file.name}")

    # 2. メール自動配信
    report_title = f"【週次レポート】地政学・マクロ経済と3つの未来シナリオ ({now.strftime('%Y年第%W週')})"
    send_report_email(report_title, response.text)


if __name__ == "__main__":
    generate_weekly_report()