import sys
import json
import urllib.request

input_text = sys.stdin.read().strip() if not sys.stdin.isatty() else "水漏れですね。明日業者を行かせます。"

prompt = f"""あなたは賃貸住宅の管理会社・オーナー側の厳格な問い合わせ対応監査エンジン（Jev）です。
以下の「入居者への返信案」を精査し、指定のJSON形式のみで出力してください。

【評価基準】
1. 丁寧さと共感: 入居者の不便や不安に寄り添う表現があるか。
2. リスク回避: 現地未確認の段階で「全額負担します」「明日確実に直ります」など安易な確約をしていないか。
3. 一時対応の指示: 水漏れ時の止水栓案内や写真撮影の依頼など、被害拡大を防ぐ具体的な指示が含まれているか。
4. 状況確認: 訪問日時の調整を「候補日の提示」として投げかけているか。

【判定ルール】
- 安易な費用負担の確約や、一次対応の指示がない場合は「FAIL」とする。
- 丁寧でリスクを避け、次のアクションが明確な場合は「PASS」とする。

【評価対象（返信案）】
{input_text}

【出力形式（JSONのみ）】
{{
  "verdict": "PASS" または "FAIL",
  "score": 0.0から1.0の数値,
  "feedback": "評価理由と、改善すべき具体的なアドバイス"
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
        parsed = json.loads(data.get("response", "{}"))
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
except Exception as e:
    fallback = {
        "verdict": "ERROR",
        "score": 0.0,
        "feedback": f"評価実行エラー: {str(e)}"
    }
    print(json.dumps(fallback, ensure_ascii=False, indent=2))