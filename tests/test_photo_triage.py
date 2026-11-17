#!/usr/bin/env python3
"""
tests/test_photo_triage.py
案2-A（photo_triage.py）のオフライン単体テストスイート。
モック／合成画像を用いて、再撮影フォールバック(-x)・札幌寒冷地安全ガード・
自己解決3項目Exit Ticket・Pydantic検証・mail_triage_bot連携タグを検証する。
"""

from __future__ import annotations

import json
import sys
from email.message import EmailMessage
from pathlib import Path

import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JEV_DEMO_DIR = PROJECT_ROOT / "antigravity-Jev-demo"
if str(JEV_DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(JEV_DEMO_DIR))

import mail_triage_bot  # noqa: E402
from photo_triage import (  # noqa: E402
    PhotoDiagnosisResult,
    format_lane_subject_tag,
    triage_photo_inquiry,
)

# 最小の有効PNGバイト列（合成画像ダミー）
DUMMY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc`\x00\x00"
    b"\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_dark_or_blurry_photo_triggers_retry_fallback(tmp_path: Path) -> None:
    """1. 暗所・ピンボケ画像 -> AUTO_REJECT(RETRY_PHOTO) & Positive Framing再撮影ガイド"""
    img_path = tmp_path / "dark_boiler.png"
    img_path.write_bytes(DUMMY_PNG_BYTES)

    def mock_vision_dark(_prompt: str, _img: bytes) -> str:
        return json.dumps(
            {
                "image_quality_ok": False,
                "quality_issue": "暗所",
                "equipment_category": "不明",
                "lane": "AUTO_APPROVE",  # 誤ってAPPROVEを返しても安全ゲートでAUTO_REJECTへ補正されること
                "rejection_reason": "NONE",
                "confidence": 0.20,
                "risk_prob": 0.80,
                "math_signal": {"urgency_level": 2, "is_winter_freeze_risk": False},
                "escalation_summary_for_owner": None,
                "reply_text": "推測ですがリセットボタンを押してください。",
            },
            ensure_ascii=False,
        )

    res = triage_photo_inquiry(
        image_input=img_path,
        tenant_message="給湯器が暗くてよく見えませんが動かないです",
        vision_client=mock_vision_dark,
    )

    assert res.image_quality_ok is False
    assert res.lane == "AUTO_REJECT"
    assert res.rejection_reason == "RETRY_PHOTO"
    assert "フラッシュ" in res.reply_text
    assert "30cm" in res.reply_text
    assert "①" in res.reply_text and "②" in res.reply_text and "③" in res.reply_text
    assert format_lane_subject_tag(res) == "[🛑送信不可・自動差戻し]"


def test_winter_freeze_and_leak_enforces_human_review_and_safety_guards() -> None:
    """2. 冬期水道凍結・漏水疑い -> 蛇口閉鎖Do Now + 熱湯禁止 + HUMAN_REVIEW"""

    def mock_vision_freeze(_prompt: str, _img: bytes) -> str:
        return json.dumps(
            {
                "image_quality_ok": True,
                "quality_issue": "なし",
                "equipment_category": "水抜き栓・元栓",
                "lane": "AUTO_APPROVE",  # モックが甘くても札幌安全ガードでHUMAN_REVIEWへ引き上げ
                "rejection_reason": "NONE",
                "confidence": 0.90,
                "risk_prob": 0.05,
                "math_signal": {"urgency_level": 5, "is_winter_freeze_risk": True},
                "escalation_summary_for_owner": None,
                "reply_text": "お部屋の暖房をつけて室温を上げ、しばらく様子を見てみてください。",
            },
            ensure_ascii=False,
        )

    def mock_jev_winter(_draft: str) -> dict:
        return {"verdict": "PASS", "score": 0.95, "feedback": "安全基準適合"}

    res = triage_photo_inquiry(
        image_input=DUMMY_PNG_BYTES,
        tenant_message="朝から水が出ません。凍結と少し水漏れがある気がします。",
        vision_client=mock_vision_freeze,
        jev_winter_evaluator=mock_jev_winter,
    )

    assert res.lane == "HUMAN_REVIEW"
    assert "蛇口" in res.reply_text and "閉め" in res.reply_text
    assert "熱湯" in res.reply_text
    assert res.escalation_summary_for_owner is not None
    assert "①" in res.reply_text and "②" in res.reply_text and "③" in res.reply_text
    assert format_lane_subject_tag(res) == "[⚠️要よっちゃん確認]"


def test_breaker_or_boiler_reset_returns_auto_approve_with_exit_ticket() -> None:
    """3. ブレーカー落ち・給湯器エラー表示 -> 安全な自己解決手順 + 3項目Exit Ticket付 AUTO_APPROVE"""

    def mock_vision_breaker(_prompt: str, _img: bytes) -> str:
        return json.dumps(
            {
                "image_quality_ok": True,
                "quality_issue": "なし",
                "equipment_category": "ブレーカー",
                "lane": "AUTO_APPROVE",
                "rejection_reason": "NONE",
                "confidence": 0.94,
                "risk_prob": 0.03,
                "math_signal": {"urgency_level": 2, "is_winter_freeze_risk": False},
                "escalation_summary_for_owner": None,
                "reply_text": (
                    "お写真を確認いたしました。安全ブレーカーの1箇所が「切」の位置に落ちています。\n"
                    "【手順】\n"
                    "1. 該当する家電（電子レンジ・ドライヤー等）のプラグを1つ抜いてください。\n"
                    "2. 下がっている小さなスイッチを「入（上）」へ押し上げてください。"
                ),
            },
            ensure_ascii=False,
        )

    res = triage_photo_inquiry(
        image_input=DUMMY_PNG_BYTES,
        tenant_message="キッチンの電気だけ消えました。ブレーカーの写真を送ります。",
        vision_client=mock_vision_breaker,
    )

    assert res.lane == "AUTO_APPROVE"
    assert res.equipment_category == "ブレーカー"
    assert "入（上）" in res.reply_text
    assert "①" in res.reply_text and "②" in res.reply_text and "③" in res.reply_text
    assert format_lane_subject_tag(res) == "[✅Jev自動承認済]"


def test_photo_diagnosis_result_pydantic_validation() -> None:
    """4. PhotoDiagnosisResult の Pydantic v2 厳格バリデーション確認"""
    with pytest.raises(ValidationError):
        PhotoDiagnosisResult(
            image_quality_ok=True,
            quality_issue="なし",
            equipment_category="ブレーカー",
            lane="AUTO_APPROVE",
            rejection_reason="NONE",
            confidence=1.5,  # 範囲外 (> 1.0)
            risk_prob=0.05,
            math_signal={"urgency_level": 2, "is_winter_freeze_risk": False},
            reply_text="これはテスト用の十分な長さの返信テキストです。",
        )


def test_mail_triage_bot_photo_hook_and_no_image_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """5. mail_triage_bot 連携: 添付画像ありは photo_triage、添付なしは既存フロー維持"""
    monkeypatch.setattr(mail_triage_bot, "reports_dir", tmp_path)

    # (A) 画像添付ありのメール
    msg_with_img = EmailMessage()
    msg_with_img["Subject"] = "ブレーカー写真"
    msg_with_img.set_content("キッチンのブレーカーが落ちました。")
    msg_with_img.add_attachment(DUMMY_PNG_BYTES, maintype="image", subtype="png", filename="breaker.png")

    extracted = mail_triage_bot.extract_first_image_attachment(msg_with_img)
    assert extracted == DUMMY_PNG_BYTES

    def mock_vision_ok(_prompt: str, _img: bytes) -> str:
        return json.dumps(
            {
                "image_quality_ok": True,
                "quality_issue": "なし",
                "equipment_category": "ブレーカー",
                "lane": "AUTO_APPROVE",
                "rejection_reason": "NONE",
                "confidence": 0.92,
                "risk_prob": 0.04,
                "math_signal": {"urgency_level": 2, "is_winter_freeze_risk": False},
                "escalation_summary_for_owner": None,
                "reply_text": "安全ブレーカーのスイッチを「入（上）」へ押し上げてください。",
            },
            ensure_ascii=False,
        )

    reply, category, verdict, lane, prefix = mail_triage_bot.process_inquiry_with_optional_photo(
        "キッチンのブレーカーが落ちました。",
        image_bytes=extracted,
        vision_client=mock_vision_ok,
        jev_winter_evaluator=lambda _d: {"verdict": "PASS", "score": 0.95},
    )
    assert category == "photo_triage"
    assert lane == "AUTO_APPROVE"
    assert prefix == "[✅Jev自動承認済]"
    assert "①" in reply and "③" in reply
    assert any(p.name.startswith("Audit_photo_triage_") for p in tmp_path.iterdir())

    # (B) 画像添付なしのメール -> 既存 generate_audited_reply_routed が呼ばれること
    msg_no_img = EmailMessage()
    msg_no_img["Subject"] = "水漏れ相談"
    msg_no_img.set_content("シンク下から水漏れしています。")
    assert mail_triage_bot.extract_first_image_attachment(msg_no_img) is None

    called = {"flag": False}

    def fake_routed(inquiry: str):
        called["flag"] = True
        return "既存ルート返信", "mail_triage_concierge", "PASS", "AUTO_APPROVE", "[✅Jev自動承認済]"

    monkeypatch.setattr(mail_triage_bot, "generate_audited_reply_routed", fake_routed)
    res_no_img = mail_triage_bot.process_inquiry_with_optional_photo(
        "シンク下から水漏れしています。",
        image_bytes=None,
    )
    assert called["flag"] is True
    assert res_no_img[1] == "mail_triage_concierge"
