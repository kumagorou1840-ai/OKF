#リンク分類監査エンジン
import sys
import json
import urllib.request

input_text = sys.stdin.read().strip() if not sys.stdin.isatty() else "{}"

prompt = f"""あなたは個人ナレッジベース（Obsidian）の厳格なリンク分類監査エンジン（Jev）です。
以下の「Webリンクの分類結果（JSON）」を精査し、指定のJSON形式で評価を出力してください。

【許容されるメインカテゴリ】
1. `real_estate` (賃貸経営、不動産市況、税務、修繕・設備)
2. `tech_ai` (Python、LLM、ローカルモデル、Agent、MCP、Obsidian連携)
3. `math_science` (線形代数、統計学、群論、解析学、物理シミュレーション)
4. `economy_geopolitics` (経済動向、金利、地政学、債券、市況分析)
5. `general_reading` (歴史、読書ノート、思想、その他)

【評価基準】
1. 根拠（Justification）の妥当性:
   - 記事タイトルや概要に対して、選定されたカテゴリの根拠が明確かつ客観的か。
2. カテゴリの単一性と厳密性:
   - 許容カテゴリ外の勝手な分類を作っていないか。
   - 複数分野にまたがる場合、最も主眼が置かれている1つに絞り込めているか。
3. タグの正規化:
   - タグが多すぎず（2〜4個程度）、階層形式（例: `tech/python`, `real_estate/maintenance`）で整理されているか。

【判定ルール】
- 根拠が薄弱、カテゴリが許容外、または複数カテゴリで迷って曖昧な場合は「FAIL」とする。
- 根拠とカテゴリが完全に一致し、タグも整理されていれば「PASS」とする。

【評価対象】
{input_text}

【出力形式（JSONのみ）】
{{
  "verdict": "PASS" または "FAIL",
  "score": 0.0から1.0の数値,
  "feedback": "評価理由と、改善すべき分類・タグの具体的な指示"
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
    with urllib.request.urlopen(req, timeout=90) as res:
        data = json.loads(res.read().decode("utf-8"))
        parsed = json.loads(data.get("response", "{}"))
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
except Exception as e:
    fallback = {"verdict": "ERROR", "score": 0.0, "feedback": str(e)}
    print(json.dumps(fallback, ensure_ascii=False, indent=2))