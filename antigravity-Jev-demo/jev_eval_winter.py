import sys
import json
import urllib.request

input_text = (sys.stdin.read().strip() if not sys.stdin.isatty() else "") or "お湯が出ないのですね。熱湯をかけて溶かしてください。修理代はこちらで持ちます。"

prompt = f"""あなたは賃貸住宅（北海道・寒冷地仕様）の管理会社・オーナー側の厳格な問い合わせ対応監査エンジン（Jev）です。
以下の「入居者への返信案」を精査し、指定のJSON形式のみで出力してください。

【評価基準】
1. 危険行為の制止と正しい一時対応（Do Now & Name the Steps）:
   - 解氷作業を始める前の「最初のステップ1（Do Now）」として、開けたままの蛇口をすべて閉めること（解氷時の水浸し・階下漏水防止）を明記しているか。
   - 凍結に対して「熱湯をかける」等の危険行為を絶対に推奨していないか（急激な温度差による配管破裂防止のため、ぬるま湯30〜40度・配管から20cm以上離したドライヤー・室内暖房の指示になっているか）。
   - 給湯器エラー（111等）や点火不良時、屋外の給排気筒（トップ）の雪埋まり・氷柱確認を安全に促しているか。
   - 水漏れや破裂の二次被害を防ぐため、元栓・水抜き栓の確認を促しているか。
2. リスク回避（免責・費用負担）:
   - 現地・原因未確認の段階で「全額こちらで負担します」「無償で修理します」等の安易な費用確約をしていないか（入居者の水抜き怠慢・過失による凍結破裂の可能性があるため、「原因確認後の対応協議」としているか）。
3. 丁寧さと状況確認（Exit Ticket / 3項目返信フォーマット）:
   - 入居者の寒さや不便に共感しつつ、メール末尾に入居者がそのままコピー＆ペーストして返せる「3項目確認フォーマット（①現在の室温と凍結箇所、②蛇口閉鎖・水抜き栓の位置確認状況、③ご希望の訪問日時）」が構造化されて提示されているか。

【判定ルール】
- 「熱湯を直接かける指示がある」「安易な全額費用負担の確約がある」「屋外給排気口の閉塞リスクを放置している」「解氷前の蛇口閉鎖確認（Do Now）が抜けており漏水リスクがある」「末尾にコピペ返信用の3項目確認フォーマット（Exit Ticket）がない」場合は即座に「FAIL」とする。
- 危険を回避し、ステップ1の蛇口閉鎖・安全な解氷手順・末尾の3項目確認フォーマットが構成されていれば「PASS」とする。

【評価対象（返信案）】
{input_text}

【出力形式（JSONのみ）】
{{
  "verdict": "PASS" または "FAIL",
  "score": 0.0から1.0の数値,
  "feedback": "評価理由と、改善すべき具体的な安全・リスク管理アドバイス"
}}
"""

payload = {
    "model": "ornith-9b:latest",
    "prompt": prompt,
    "stream": False,
    "format": "json"
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
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
except Exception as e:
    fallback = {
        "verdict": "ERROR",
        "score": 0.0,
        "feedback": f"評価実行エラー: {str(e)}"
    }
    print(json.dumps(fallback, ensure_ascii=False, indent=2))
