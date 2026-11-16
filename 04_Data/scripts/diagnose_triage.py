import os
import sys
import sqlite3
import json
from enum import Enum
from typing import List, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from PIL import Image

# 1. 汎用4分類（トリアージ体系）の定義
class TriageType(str, Enum):
    TYPE_A = "Type_A_Immediate_Shutoff"    # 即時遮断・応急処置（止水・通電遮断など被害拡大防止）
    TYPE_B = "Type_B_Self_Reset"          # セルフリセット（ブレーカー・電源抜去・ガスメーター復帰）
    TYPE_C = "Type_C_Info_Gathering"      # 機器故障・型番収集（業者手配の前提情報収集）
    TYPE_D = "Type_D_Rule_And_Guidance"   # 消耗品・規約案内・過失防止注意喚起

# 2. 構造化出力（JSONスキーマ）の定義
class DiagnosticResult(BaseModel):
    triage_type: TriageType = Field(description="トラブルの汎用トリアージ分類（Type A〜D）")
    urgency_level: str = Field(description="緊急度（High / Medium / Low）")
    detected_device: str = Field(description="写真から特定された器具・機器名")
    observation: str = Field(description="写真および状況説明から読み取った現状")
    action_steps: List[str] = Field(description="入居者に案内する安全な自己解決手順（3ステップ以内）")
    notify_landlord: bool = Field(description="大家・管理会社への即時通知が必要かどうか（True/False）")
    internal_memo: Optional[str] = Field(description="管理者向けメモ（交換部材や過失リスク等の示唆）")

# 3. 案件履歴をSQLiteに保存する関数
def save_to_database(room_no: str, user_msg: str, res: DiagnosticResult, db_path="04_Data/raw/trouble_history.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO incidents (
            room_no, detected_device, triage_type, urgency_level,
            user_message, observation, action_steps, notified_landlord, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        room_no,
        res.detected_device,
        res.triage_type.value,
        res.urgency_level,
        user_msg,
        res.observation,
        json.dumps(res.action_steps, ensure_ascii=False),
        1 if (res.notify_landlord or res.triage_type == TriageType.TYPE_A) else 0,
        "要業者手配" if res.notify_landlord else "対応中"
    ))
    record_id = cur.lastrowid
    conn.commit()
    conn.close()
    return record_id

# 4. 大家向け緊急通知の送信関数（シミュレーション・Webhook対応枠）
def send_landlord_alert(record_id: int, room_no: str, res: DiagnosticResult):
    print("\n" + "!" * 50)
    print(f"【大家・管理者への緊急通知送信 (ID: {record_id})】")
    print(f"◆ 物件・部屋番号: {room_no}")
    print(f"◆ 発生事象: {res.detected_device}（{res.triage_type.value} / 緊急度: {res.urgency_level}）")
    print(f"◆ 現状: {res.observation}")
    print(f"◆ 管理メモ: {res.internal_memo or '特になし'}")
    print("◆ 案内状況: 入居者へ初期止水/遮断の手順を自動案内済みです。")
    print("!" * 50 + "\n")

def run_diagnosis(image_path: str, user_message: str, room_no: str = "101号室"):
    if not os.path.exists(image_path):
        print(f"[エラー] 画像ファイルが見つかりません: {image_path}")
        return

    client = genai.Client()
    img = Image.open(image_path)

    system_instruction = (
        "あなたは賃貸管理のAIコンシェルジュです。"
        "入居者からの写真とメッセージを診断し、危険作業は指示せず、"
        "安全最優先でトリアージ分類（Type A〜D）と3ステップ以内の手順を返してください。"
    )

    print(f">> 診断開始（対象部屋: {room_no}）")
    print(f">> 相談内容: {user_message}\n")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[img, f"入居者からの相談内容: {user_message}"],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DiagnosticResult,
            system_instruction=system_instruction,
            temperature=0.2,
        ),
    )

    result: DiagnosticResult = response.parsed

    # 入居者向け回答の表示
    print("=" * 45)
    print(f"【判定分類】: {result.triage_type.value}")
    print(f"【緊急度】  : {result.urgency_level}")
    print(f"【特定設備】: {result.detected_device}")
    print(f"【状況確認】: {result.observation}")
    print("【入居者への案内手順】:")
    for i, step in enumerate(result.action_steps, 1):
        print(f"  {i}. {step}")
    print("=" * 45)

    # データベースへ保存
    record_id = save_to_database(room_no, user_message, result)
    print(f"\n>> [DB] 案件履歴を保存しました（レコードID: {record_id}）")

    # 大家向け通知の判定と実行
    if result.notify_landlord or result.triage_type == TriageType.TYPE_A:
        send_landlord_alert(record_id, room_no, result)
    else:
        print(">> [Info] 大家への緊急通知は不要（入居者自己解決を見守り中）")

if __name__ == "__main__":
    sample_image = "04_Data/raw/test_image.jpg"
    sample_message = "トイレの横から水がじわじわ漏れて止まりません。"
    sample_room = "203号室"

    if len(sys.argv) >= 3:
        sample_image = sys.argv[1]
        sample_message = sys.argv[2]
    if len(sys.argv) >= 4:
        sample_room = sys.argv[3]

    run_diagnosis(sample_image, sample_message, sample_room)
    