import sys
import json
import urllib.request

input_text = (sys.stdin.read().strip() if not sys.stdin.isatty() else "") or "隣の人がうるさいのですね。すぐに隣に注意して出て行ってもらいます。"

prompt = f"""あなたは賃貸住宅の管理会社・オーナー側の厳格な問い合わせ対応監査エンジン（Jev）です。
以下の「入居者からの騒音・生活マナー苦情に対する返信案」を精査し、指定のJSON形式のみで出力してください。

【評価基準】
1. 中立性の維持（予断の排除）:
   - 申告者の心情（不快感・睡眠不足など）に真摯に寄り添い・傾聴しつつも、相手方を一方的に「加害者」と決めつけたり、相手の非を断定していないか。
   - 「管理側としても事実関係を慎重に確認する」姿勢を保っているか。
2. 直接トラブルの抑止:
   - 入居者同士の直接対決・直接談判を促していないか（「直接言ってみてください」等の危険な指示の厳禁）。
   - まずは「全戸配布の注意喚起文」「掲示板周知」などの段階的対応を提示しているか。
3. 客観的記録（ログ）の収集依頼:
   - 感情論に終始せず、「発生日時」「音の種類（足音・重低音・声など）」「頻度」の客観的なメモ・記録を依頼しているか。
4. リスク回避（過度な確約の排除）:
   - 「すぐに退去させます」「必ず静かにさせます」「警察に通報して解決します」等の実現不能・越権的な安易な約束をしていないか。

【判定ルール】
- 相手方を一方的に加害者と断定している、直接交渉を促している、または安易な退去確約がある場合は「FAIL」とする。
- 共感・中立性・記録の依頼・段階的周知（ポスティング等）の案内が揃っていれば「PASS」とする。

【評価対象（返信案）】
{input_text}

【出力形式（JSONのみ）】
{{
  "verdict": "PASS" または "FAIL",
  "score": 0.0から1.0の数値,
  "feedback": "評価理由と、改善すべき具体的なリスク管理・文面推敲アドバイス"
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
