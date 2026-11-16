import sys
import json
import urllib.request

input_text = (sys.stdin.read().strip() if not sys.stdin.isatty() else "") or "隣の人がうるさいのですね。すぐに隣に注意して出て行ってもらいます。"

prompt = f"""あなたは賃貸住宅の管理会社・オーナー側の厳格な問い合わせ対応監査エンジン（Jev）です。
以下の「入居者からの騒音・生活マナー苦情に対する返信案」を精査し、指定のJSON形式のみで出力してください。

【評価基準】
1. 中立性の維持と Positive Framing（味方としての証拠固め説明）:
   - 申告者の心情（不快感・睡眠不足など）に真摯に寄り添い・傾聴しつつも、調査前の段階で相手方を一方的に「加害者」と断定していないか。
   - 建物構造上の音の回り込み（上下・斜め等）を説明する際、申告者を疑うニュアンスではなく、「今後、管理会社から実効性のある強い措置（個別注意や契約上の警告）をとる際に相手が言い逃れできない『客観的証拠（外堀）』を固めるため」という味方としての理由説明（Positive Framing / Explain Everything）になっているか。
2. 直接トラブルの抑止と緊急時（事件性）の安全境界:
   - 入居者同士の直接対決・直接談判を促していないか（「直接言ってみてください」等の危険な指示の厳禁）。
   - まずは「全戸配布の注意喚起文」「掲示板周知」などの段階的対応を提示しているか。
   - 激しい怒鳴り声・暴行音・物の破損音など事件性や身の危険を感じる緊急時は、管理会社の返信を待たず直ちに警察（110番）へ通報するよう案内しているか。
3. 客観的記録（ログ）の収集依頼と末尾3項目 Exit Ticket:
   - メール末尾に、入居者がそのままコピー＆ペーストして返せる「3項目確認フォーマット（Exit Ticket：①発生日時・時間帯と継続時間、②音が響く物理的方向［壁・天井・床など］と音の種類、③事件性・緊急性の有無）」が構造化されて提示されているか。
4. リスク回避（過度な確約の排除）:
   - 「すぐに退去させます」「必ず静かにさせます」等の実現不能・越権的な安易な約束をしていないか。

【判定ルール】
- 相手方を一方的に加害者と断定している、直接交渉を促している、安易な退去確約がある、「強い措置をとるための客観的証拠固め（Positive Framing）」の説明がない、緊急時（事件性）の110番案内がない、または末尾にコピペ返信用の3項目確認フォーマット（Exit Ticket）がない場合は即座に「FAIL」とする。
- 共感・中立性・Positive Framing（証拠固めの理由説明）・直接交渉禁止・緊急時110番案内・段階的周知・末尾の3項目確認フォーマットがすべて揃っていれば「PASS」とする。

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
