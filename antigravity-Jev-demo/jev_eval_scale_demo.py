import sys
import json
import urllib.request

MODEL_NAME = "ornith-9b:latest"


def evaluate_reply_scale(input_text: str) -> dict:
    prompt = f"""あなたは賃貸住宅の管理会社・オーナー側の厳格な問い合わせ対応監査エンジン（Jev）です。
以下の「入居者への返信案」を精査し、各項目を「5段階スケール（1〜5）」および「定性ランク（S / A / B / C）」で評価し、指定のJSON形式のみで出力してください。

【評価項目と5段階ルーブリック（基準）】
1. `empathy_level` (共感・丁寧さ):
   - 5: 深いお詫びと生活不便への具体的な配慮がある
   - 3: 最低限の挨拶・お詫びのみ
   - 1: 事務的・突き放す表現、またはお詫びが一切ない
2. `risk_control_level` (免責・リスク管理):
   - 5: 現地確認後に原因特定・費用協議する旨が明確で、安易な確約がない
   - 3: 危険な確約はないが、費用や原因確認の説明がやや不足
   - 1: 現地未確認で「全額負担します」「確実に直ります」等の危険な確約をしている
3. `action_clarity_level` (一時対応・日程打診の具体性):
   - 5: 止水栓・写真撮影の指示と、複数の訪問日時候補の打診が揃っている
   - 3: 一時対応または日程打診のどちらか一方のみ記載されている
   - 1: 具体的な指示がなく「明日行かせます」等の一方的な通告のみ

【定性ランク（qualitative_grade）の定義】
- `"S"`: 模範的（全項目が 5）
- `"A"`: 良好・送信可能（全項目が 3 以上、かつ平均 4.0 以上）
- `"B"`: 要推敲（一部に 2 以下の不足がある）
- `"C"`: 危険・送信不可（1 の項目が含まれる、または重大な確約リスクがある）

【判定ルール】
- 定性ランクが `"S"` または `"A"`（全項目3以上かつ平均4.0以上）の場合のみ `"verdict": "PASS"` とし、`"B"` または `"C"` は `"verdict": "FAIL"` とする。

【評価対象（返信案）】
{input_text}

【出力形式（JSONのみ）】
{{
  "scales": {{
    "empathy_level": 1から5の整数,
    "risk_control_level": 1から5の整数,
    "action_clarity_level": 1から5の整数
  }},
  "qualitative_grade": "S" または "A" または "B" または "C",
  "verdict": "PASS" または "FAIL",
  "score": 0.0から1.0の数値,
  "feedback": "各段階の判定理由と、ランクS/Aに引き上げるための具体的な改善アドバイス"
}}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0}
    }

    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as res:
            data = json.loads(res.read().decode("utf-8"))
            raw_resp = data.get("response", "{}")
            if "</think>" in raw_resp:
                raw_resp = raw_resp.split("</think>")[-1].strip()
            parsed = json.loads(raw_resp)

            # Python側での確定的な段階（スケール）閾値ガード
            scales = parsed.get("scales", {})
            if scales:
                vals = [int(v) for v in scales.values()]
                avg_scale = sum(vals) / len(vals)
                min_scale = min(vals)
                parsed["score"] = round(avg_scale / 5.0, 2)

                if min_scale == 5:
                    parsed["qualitative_grade"] = "S"
                    parsed["verdict"] = "PASS"
                elif min_scale >= 3 and avg_scale >= 4.0:
                    parsed["qualitative_grade"] = "A"
                    parsed["verdict"] = "PASS"
                elif min_scale >= 2:
                    parsed["qualitative_grade"] = "B"
                    parsed["verdict"] = "FAIL"
                else:
                    parsed["qualitative_grade"] = "C"
                    parsed["verdict"] = "FAIL"

            return parsed
    except Exception as e:
        return {
            "scales": {},
            "qualitative_grade": "ERROR",
            "verdict": "ERROR",
            "score": 0.0,
            "feedback": f"評価実行エラー: {str(e)}"
        }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        samples = [("引数指定テキスト", sys.argv[1])]
    else:
        samples = [
            (
                "① 低ランク文面テスト（ランクC・FAIL になる例）",
                "水漏れですね。明日業者を行かせます。修理代は全額こちらで負担しますので安心してください。"
            ),
            (
                "② 中間ランク文面テスト（ランクB・一部不足で FAIL になる例）",
                "水漏れでご不便をおかけし申し訳ございません。現地で原因を確認して対応をご相談いたしますので、明日10時に業者が伺います。"
            ),
            (
                "③ 高ランク文面テスト（ランクS/A・PASS になる例）",
                "水漏れでご不便をおかけし誠に申し訳ございません。被害拡大防止のため止水栓を閉め、水漏れ箇所の写真撮影をお願いいたします。現地で原因を確認した上で費用や修繕方法を協議させてください。明日10時または14時でご訪問可能ですがご都合いかがでしょうか。"
            ),
        ]

    for title, text in samples:
        print(f"\n=== {title} ===", flush=True)
        print(f"入力文面: {text}", flush=True)
        result = evaluate_reply_scale(text)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
