import sys
import json
import urllib.request

MODEL_NAME = "ornith-9b:latest"


def evaluate_reply_prob(input_text: str) -> dict:
    prompt = f"""あなたは賃貸住宅の管理会社・オーナー側の厳格な問い合わせ対応監査エンジン（Jev）です。
以下の「入居者への返信案」を送信した場合に起こりうる事象の「確率（0.00〜1.00）」と、監査自身の「確信度（confidence: 0.00〜1.00）」を推定し、指定のJSON形式のみで出力してください。

【確率（0.00〜1.00）の推定項目】
1. `trouble_escalation_prob` (クレーム・炎上発展確率):
   - 冷淡な表現や一方的な通告により、入居者の怒りや二次クレームに発展する確率（0.00=極めて安全 〜 1.00=確実に炎上）
2. `financial_loss_prob` (不当な費用負担・損失発生確率):
   - 現地未確認での安易な無償修理・全額負担の確約により、本来不要な金銭的損失を被る確率（0.00=リスクなし 〜 1.00=損失確定）
3. `smooth_resolution_prob` (スムーズな一次対応・日程合意確率):
   - 入居者が迷わず止水栓・写真撮影を行い、1往復で訪問日程が決まる確率（0.00=行動不能 〜 1.00=確実に合意）
4. `confidence` (Jev監査の確信度):
   - 入力文面の情報量から、この確率推定がどれほど確実か（0.00=情報不足で判断困難 〜 1.00=確信あり）

【判定ルール（確率閾値）】
- `trouble_escalation_prob` が `0.30` 未満、かつ `financial_loss_prob` が `0.20` 未満、かつ `smooth_resolution_prob` が `0.75` 以上の場合のみ `"verdict": "PASS"` とする。それ以外は `"verdict": "FAIL"` とする。

【評価対象（返信案）】
{input_text}

【出力形式（JSONのみ）】
{{
  "probabilities": {{
    "trouble_escalation_prob": 0.00から1.00の小数,
    "financial_loss_prob": 0.00から1.00の小数,
    "smooth_resolution_prob": 0.00から1.00の小数,
    "confidence": 0.00から1.00の小数
  }},
  "verdict": "PASS" または "FAIL",
  "score": 0.00から1.00の数値,
  "feedback": "各確率の算出根拠と、リスク確率を下げて解決確率を上げるための具体的な改善アドバイス"
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

            # Python側での確定的な確率閾値（リスク許容度スライダー）ガード
            probs = parsed.get("probabilities", {})
            if probs:
                p_trouble = float(probs.get("trouble_escalation_prob", 1.0))
                p_loss = float(probs.get("financial_loss_prob", 1.0))
                p_smooth = float(probs.get("smooth_resolution_prob", 0.0))
                conf = float(probs.get("confidence", 1.0))

                # 総合安全スコア = 解決確率 × (1 - 最大リスク確率)
                max_risk = max(p_trouble, p_loss)
                parsed["score"] = round(p_smooth * (1.0 - max_risk), 2)

                # リスク確率が許容ラインを超えたら強制 FAIL
                if p_trouble >= 0.30 or p_loss >= 0.20 or p_smooth < 0.75:
                    parsed["verdict"] = "FAIL"
                elif conf < 0.70:
                    # 確信度が低い場合は人間確認を促すため FAIL 扱い
                    parsed["verdict"] = "FAIL"
                else:
                    parsed["verdict"] = "PASS"

            return parsed
    except Exception as e:
        return {
            "probabilities": {},
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
                "① 高リスク文面テスト（炎上・損失確率が高く FAIL になる例）",
                "水漏れですね。明日業者を行かせます。修理代は全額こちらで負担しますので安心してください。"
            ),
            (
                "② 低リスク・高解決確率文面テスト（リスク確率が低く PASS になる例）",
                "水漏れでご不便をおかけし誠に申し訳ございません。被害拡大防止のため止水栓を閉め、水漏れ箇所の写真撮影をお願いいたします。現地で原因を確認した上で費用や修繕方法を協議させてください。明日10時または14時でご訪問可能ですがご都合いかがでしょうか。"
            ),
        ]

    for title, text in samples:
        print(f"\n=== {title} ===", flush=True)
        print(f"入力文面: {text}", flush=True)
        result = evaluate_reply_prob(text)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
