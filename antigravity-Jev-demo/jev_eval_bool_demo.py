import sys
import json
import urllib.request

MODEL_NAME = "ornith-9b:latest"


def evaluate_reply_bool(input_text: str) -> dict:
    prompt = f"""あなたは賃貸住宅の管理会社・オーナー側の厳格な問い合わせ対応監査エンジン（Jev）です。
以下の「入居者への返信案」に書かれている事実のみを厳密に精査し、書かれていないことは必ず false として、指定のJSON形式のみで出力してください。

【評価基準（二値判定：true / false）】
1. `has_empathy` (丁寧さと共感): お詫びや入居者の不便・不安に寄り添う言葉が明記されているか（明記されていれば true、無ければ false）
2. `no_risky_promise` (免責・リスク回避): 現地未確認で「全額負担します」「確実に直ります」等の危険な確約をしていないか（確約していなければ true、安易に確約していたら false）
3. `has_first_aid` (一時対応の指示): 「止水栓（元栓）を閉める」「写真を撮る」など被害拡大を防ぐ具体的な指示が明記されているか（明記されていれば true、無ければ false）
4. `has_schedule_check` (日程調整の打診): 訪問日時の候補提示や都合の確認が明記されているか（明記されていれば true、一方的な通告のみなら false）

【判定ルール】
- 上記4つのブール値（true / false）が **すべて `true`** の場合のみ `"verdict": "PASS"` とし、1つでも `false` があれば `"verdict": "FAIL"` とする。

【評価対象（返信案）】
{input_text}

【出力形式（JSONのみ）】
{{
  "checks": {{
    "has_empathy": true または false,
    "no_risky_promise": true または false,
    "has_first_aid": true または false,
    "has_schedule_check": true または false
  }},
  "verdict": "PASS" または "FAIL",
  "score": 0.0から1.0の数値,
  "feedback": "falseになった項目と、改善すべき具体的なアドバイス"
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

            # Python側での確定的な二値（bool）チェック強制ガード
            checks = parsed.get("checks", {})
            if checks and not all(bool(v) is True for v in checks.values()):
                parsed["verdict"] = "FAIL"

            return parsed
    except Exception as e:
        return {
            "checks": {},
            "verdict": "ERROR",
            "score": 0.0,
            "feedback": f"評価実行エラー: {str(e)}"
        }


if __name__ == "__main__":
    # 引数があればそれを評価、なければ NG例 と OK例 の2パターンを自動比較
    if len(sys.argv) > 1:
        samples = [("引数指定テキスト", sys.argv[1])]
    else:
        samples = [
            (
                "① NG文面テスト（falseが含まれ FAIL になる例）",
                "水漏れですね。明日業者を行かせます。修理代は全額こちらで負担しますので安心してください。"
            ),
            (
                "② OK文面テスト（すべてtrueで PASS になる例）",
                "水漏れでご不便をおかけし誠に申し訳ございません。被害拡大防止のため止水栓を閉め、水漏れ箇所の写真撮影をお願いいたします。現地で原因を確認した上で費用や修繕方法を協議させてください。明日10時または14時でご訪問可能ですがご都合いかがでしょうか。"
            ),
        ]

    for title, text in samples:
        print(f"\n=== {title} ===", flush=True)
        print(f"入力文面: {text}", flush=True)
        result = evaluate_reply_bool(text)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
