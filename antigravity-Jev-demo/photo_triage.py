#!/usr/bin/env python3
"""
antigravity-Jev-demo/photo_triage.py
案2-A（写真診断・自己解決誘導）基本プロンプト設計書に基づく写真トリアージモジュール。
`mail_triage_bot.py` からインポートして呼び出し、必要に応じて `jev_eval_winter.py` と連携する。
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Callable, Dict, Literal, Optional, Union

from pydantic import BaseModel, Field

DEMO_DIR = Path(__file__).resolve().parent
DEFAULT_VISION_MODEL = "gemma4:26b"

WINTER_FREEZE_KEYWORDS = ("凍結", "凍っ", "お湯が出ない", "水が出ない", "水抜き", "解氷", "給湯器")
EMERGENCY_KEYWORDS = ("漏水", "水漏れ", "ガス臭", "破裂", "異臭", "煙", "火花")

PHOTO_DIAGNOSIS_SYSTEM_PROMPT = """# Role
あなたは北海道札幌市の賃貸物件（寒冷地・冬期凍結や設備エラー対応を含む）専属の「入居者AIコンシェルジュ（写真診断・一次切り分け担当）」です。
入居者から送信された設備の写真（ブレーカー、給湯器リモコン、水抜き栓、配管周辺など）と相談テキストを解析し、安全かつ確実な自己解決誘導または大家（管理人）へのエスカレーション判定を、指定されたJSONフォーマットのみで出力してください。

# Step 1: 画像品質ゲート（再撮影フォールバック `-x`）
写真を解析する前に、まず以下の「4つの視認性不良条件」に該当しないか厳格に判定してください。
1. 暗所（照明不足で設備の輪郭やスイッチ文字が読めない）
2. ピンボケ・手ブレ（文字、数字、ランプ状態がぼやけている）
3. 画面反射・白飛び（フラッシュや照明の映り込みでエラー表示灯やパネルが読めない）
4. 型番・対象物の見切れ（肝心のスイッチ、元栓、エラーコードが画面枠外にある）
上記に1つでも該当する場合、絶対に推測で操作手順を案内せず、image_quality_ok=false, lane="AUTO_REJECT", rejection_reason="RETRY_PHOTO" とし、Positive Framingで再撮影ガイドを返してください。

# Step 2: 札幌・寒冷地安全＆免責ガード（Right Is Right）
1. 凍結時の最優先行動（Do Now）: 解氷や点検の前に必ず「開いている蛇口をすべて閉め切ること（解氷後の階下漏水防止）」を第1に案内すること。
2. 熱湯禁止: 配管や水抜き栓へ熱湯をかける指示は絶対に出さないこと。
3. 屋外・高所作業の回避: 夜間や積雪・落雪の危険がある屋外作業を指示せず HUMAN_REVIEW へ回すこと。
4. 費用負担の断定禁止: 現地確認前に無償修理や大家負担を確約しないこと。
5. What to Do: 「気をつけて」「適切に」「なるべく」等の曖昧語を禁止し、観察可能な具体手順で記述すること。

# Step 3: 3レーン判定基準
- AUTO_APPROVE: 画質OK・安全確認済で confidence >= 0.85 かつ risk_prob < 0.10 の自己解決案件。
- HUMAN_REVIEW: 漏水・ガス臭・凍結破裂疑い・判断保留・信頼度不足時の大家エスカレーション。
- AUTO_REJECT: 画質不良（RETRY_PHOTO）または対応範囲外（OUT_OF_SCOPE）。

# Step 4: 3項目 Exit Ticket 形式
reply_text 末尾に ①現在の確認状態、②次に試す1アクション、③解決しない場合の連絡導線 を必ず明記すること。

# Output Format（以下の全キーを含む厳格なJSONのみ出力）
{
  "image_quality_ok": true,
  "quality_issue": "なし | 暗所 | ピンボケ | 画面反射 | 型番見切れ",
  "equipment_category": "ブレーカー | 給湯器 | 水抜き栓・元栓 | 配管・水回り | その他 | 不明",
  "lane": "AUTO_APPROVE | HUMAN_REVIEW | AUTO_REJECT",
  "rejection_reason": "NONE | RETRY_PHOTO | OUT_OF_SCOPE",
  "confidence": 0.00,
  "risk_prob": 0.00,
  "math_signal": {
    "urgency_level": 1,
    "is_winter_freeze_risk": false
  },
  "escalation_summary_for_owner": null,
  "reply_text": "入居者への返信本文（3項目 Exit Ticket 必須）"
}"""


class MathSignal(BaseModel):
    """数理モデリング（緊急度・冬期凍結リスク）連携用シグナル"""

    urgency_level: int = Field(ge=1, le=5, description="緊急度 1(低)〜5(最高)")
    is_winter_freeze_risk: bool = Field(description="冬期凍結・破裂リスクの有無")


class PhotoDiagnosisResult(BaseModel):
    """案2-A 写真診断の構造化出力契約（Pydantic v2）"""

    image_quality_ok: bool
    quality_issue: Literal["なし", "暗所", "ピンボケ", "画面反射", "型番見切れ"]
    equipment_category: Literal[
        "ブレーカー", "給湯器", "水抜き栓・元栓", "配管・水回り", "その他", "不明"
    ]
    lane: Literal["AUTO_APPROVE", "HUMAN_REVIEW", "AUTO_REJECT"]
    rejection_reason: Literal["NONE", "RETRY_PHOTO", "OUT_OF_SCOPE"]
    confidence: float = Field(ge=0.0, le=1.0)
    risk_prob: float = Field(ge=0.0, le=1.0)
    math_signal: MathSignal
    escalation_summary_for_owner: Optional[str] = None
    reply_text: str = Field(min_length=20, description="3項目Exit Ticketを含む返信文")


def load_image_bytes(image_input: Union[str, Path, bytes]) -> bytes:
    """ファイルパスまたはバイト列から画像バイトを読み込む"""
    if isinstance(image_input, (bytes, bytearray)):
        data = bytes(image_input)
    elif isinstance(image_input, (str, Path)):
        path = Path(image_input)
        if not path.exists():
            raise FileNotFoundError(f"画像ファイルが見つかりません: {path}")
        data = path.read_bytes()
    else:
        raise TypeError("image_input は str, Path, bytes のいずれかである必要があります。")

    if not data:
        raise ValueError("画像データが空です。")
    return data


def call_ollama_vision(
    prompt: str,
    image_bytes: bytes,
    model: str = DEFAULT_VISION_MODEL,
) -> str:
    """ローカル Ollama Vision API (/api/chat, think=False) を呼び出して JSON テキストを返す"""
    b64_img = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [b64_img],
            }
        ],
        "stream": False,
        "think": False,
        "format": PhotoDiagnosisResult.model_json_schema(),
        "options": {"num_predict": 512},
    }
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as res:
        data = json.loads(res.read().decode("utf-8"))
        raw_resp = data.get("message", {}).get("content", "{}").strip()
        if "</think>" in raw_resp:
            raw_resp = raw_resp.split("</think>")[-1].strip()
        return raw_resp


def run_jev_winter_audit(draft_text: str) -> Dict[str, object]:
    """既存の jev_eval_winter.py をサブプロセスで呼び出し安全監査を行う"""
    script_path = DEMO_DIR / "jev_eval_winter.py"
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        input=draft_text,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    return json.loads(proc.stdout)


def _build_retry_photo_reply(issue: str) -> str:
    """Positive Framing による再撮影ガイド＋3項目 Exit Ticket を生成"""
    return (
        "お写真をお送りいただきありがとうございます。\n"
        f"現在のお写真では設備の状態が十分に確認できないため（検知理由: {issue}）、"
        "安全かつ正確にご案内できるよう、もう一度だけお写真を撮影してお送りいただけますでしょうか。\n\n"
        "【撮影のお願い（3ステップ）】\n"
        "1. スマートフォンのライト（フラッシュ）をオンにしてください。\n"
        "2. 設備（スイッチ・エラー表示灯・型番シール等）から約30cm離し、ピントが合うまで1秒待ってから正面より撮影してください（光が反射する場合は少し斜めから撮影してください）。\n"
        "3. 撮影後、そのままこちらのトークへお送りください。\n\n"
        "---\n"
        "【ご確認・次のステップ（Exit Ticket）】\n"
        "① 現在の確認状態：お写真の視認性再確認が必要です（推測での誤案内防止のため）。\n"
        "② 次に試す1アクション：フラッシュをオンにし、約30cm離して設備全体を再撮影してください。\n"
        "③ 解決しない場合の連絡導線：漏水・ガス臭など緊急の場合は再撮影せず、24時間緊急窓口へ直ちにお電話ください。"
    )


def _ensure_exit_ticket(reply_text: str, status_note: str, next_action: str) -> str:
    """返信末尾に3項目 Exit Ticket が不足していれば補完する"""
    if "①" in reply_text and "②" in reply_text and "③" in reply_text:
        return reply_text
    ticket = (
        "\n\n---\n"
        "【ご確認・次のステップ（Exit Ticket）】\n"
        f"① 現在の確認状態：{status_note}\n"
        f"② 次に試す1アクション：{next_action}\n"
        "③ 解決しない場合の連絡導線：改善しない場合や緊急時は、本メッセージへ返信（部屋番号・状況）または管理窓口へご連絡ください。"
    )
    return f"{reply_text.rstrip()}{ticket}"


def _apply_sapporo_safety_guards(
    result: PhotoDiagnosisResult,
    tenant_message: str,
    jev_winter_evaluator: Optional[Callable[[str], Dict[str, object]]] = None,
) -> PhotoDiagnosisResult:
    """画像品質ゲート(-x)および札幌寒冷地安全ガードを決定論的に強制適用する"""
    if not result.image_quality_ok:
        issue = result.quality_issue if result.quality_issue != "なし" else "暗所・不鮮明"
        return result.model_copy(
            update={
                "lane": "AUTO_REJECT",
                "rejection_reason": "RETRY_PHOTO",
                "reply_text": _build_retry_photo_reply(issue),
            }
        )

    combined_text = f"{tenant_message}\n{result.reply_text}"
    is_winter = result.math_signal.is_winter_freeze_risk or any(
        k in combined_text for k in WINTER_FREEZE_KEYWORDS
    )
    is_emergency = any(k in combined_text for k in EMERGENCY_KEYWORDS)

    updated_reply = result.reply_text
    updated_lane = result.lane
    updated_summary = result.escalation_summary_for_owner

    if is_winter or is_emergency:
        updated_lane = "HUMAN_REVIEW"
        if not updated_summary:
            updated_summary = f"札幌冬期・緊急確認要（カテゴリ: {result.equipment_category} / メッセージ: {tenant_message[:60]}）"

        # 凍結・漏水時は「蛇口を閉め切る Do Now」と「熱湯禁止」を必須補完
        safety_prefix_parts = []
        if "蛇口" not in updated_reply or "閉め" not in updated_reply:
            safety_prefix_parts.append(
                "【最優先手順（Do Now）】解氷や確認の前に、まず開いている蛇口をすべて閉め切ってください（解氷後の階下漏水防止のため）。"
            )
        if "熱湯" not in updated_reply:
            safety_prefix_parts.append(
                "【安全上の厳守事項】急激な温度差による配管破裂を防ぐため、配管や水抜き栓に熱湯は絶対に使用しないでください。"
            )
        if safety_prefix_parts:
            updated_reply = "\n".join(safety_prefix_parts) + "\n\n" + updated_reply

        if jev_winter_evaluator is not None:
            audit = jev_winter_evaluator(updated_reply)
            if str(audit.get("verdict", "")).upper() != "PASS":
                updated_lane = "HUMAN_REVIEW"

    # 信頼度・リスク閾値による安全弁
    if updated_lane == "AUTO_APPROVE" and (result.confidence < 0.85 or result.risk_prob >= 0.10):
        updated_lane = "HUMAN_REVIEW"

    updated_reply = _ensure_exit_ticket(
        updated_reply,
        status_note=f"{result.equipment_category}の一次確認を実施しました。",
        next_action="上記手順をご確認のうえ、安全に1ステップのみお試しください。"
        if updated_lane == "AUTO_APPROVE"
        else "安全確保のうえ、大家（管理人）からの折り返し連絡をお待ちください。",
    )

    return result.model_copy(
        update={
            "lane": updated_lane,
            "escalation_summary_for_owner": updated_summary,
            "reply_text": updated_reply,
        }
    )


def triage_photo_inquiry(
    image_input: Union[str, Path, bytes],
    tenant_message: str = "",
    vision_client: Optional[Callable[[str, bytes], str]] = None,
    jev_winter_evaluator: Optional[Callable[[str], Dict[str, object]]] = None,
    model: str = DEFAULT_VISION_MODEL,
) -> PhotoDiagnosisResult:
    """
    写真入力と入居者メッセージを受け取り、Pydantic v2 検証・安全ガード適用済の
    PhotoDiagnosisResult（3レーン判定 + 3項目Exit Ticket）を返す。
    """
    image_bytes = load_image_bytes(image_input)
    full_prompt = (
        f"{PHOTO_DIAGNOSIS_SYSTEM_PROMPT}\n\n"
        f"# 入居者からのメッセージ\n{tenant_message or '（テキストなし・写真のみ）'}"
    )

    client = vision_client or (lambda p, b: call_ollama_vision(p, b, model=model))
    raw_json_str = client(full_prompt, image_bytes)
    parsed = json.loads(raw_json_str)
    validated = PhotoDiagnosisResult.model_validate(parsed)

    return _apply_sapporo_safety_guards(
        validated,
        tenant_message=tenant_message,
        jev_winter_evaluator=jev_winter_evaluator,
    )


def format_lane_subject_tag(result: PhotoDiagnosisResult) -> str:
    """mail_triage_bot.py の件名タグ規約に合わせたラベルを返す"""
    if result.lane == "AUTO_APPROVE":
        return "[✅Jev自動承認済]"
    if result.lane == "HUMAN_REVIEW":
        return "[⚠️要よっちゃん確認]"
    return "[🛑送信不可・自動差戻し]"
