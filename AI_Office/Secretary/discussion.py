import requests
import json
import os
import re
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "ornith-9b:latest"
OUTPUT_DIR = r"C:\Users\PC_User\Documents\Obsidian\obsidian_1\AI_Office\Discussion_Room"

TOPIC = "B社の料金詳細調査のために、調査期間を半日延長するべきか否か。"

MEMBERS = [
    {"name": "社員A (リサーチ)", "role": "データと事実を重視。競合状況の精緻な把握が必要と主張する。"},
    {"name": "社員B (コスト採算)", "role": "費用対効果や時間コストにシビア。半日の遅延による損失を懸念し早期切り上げを主張する。"},
    {"name": "社員C (リスク管理)", "role": "規約遵守や情報収集リスクを警戒。ログイン壁を突破するリスクや代替策の有無を問う。"},
    {"name": "社員D (スピード推進)", "role": "スピード第一。完全な情報がなくても仮説を立てて前に進めるべきと主張する。"},
    {"name": "社員E (戦略立案)", "role": "顧客価値や事業戦略全体を見渡す。他社とのポジショニングの違いを整理し、合意形成を導く。"}
]

def clean_text(text):
    # <think>...</think> の除去
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # 閉じタグ単体や開きタグ単体以降の残りカスを除去
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    text = re.sub(r".*</think>", "", text, flags=re.DOTALL)
    
    # 行単位で英語主体の行（思考ログや英単語メモ）を除外
    lines = text.strip().split("\n")
    japanese_lines = []
    for line in lines:
        line_clean = line.strip().strip('"').strip("'")
        # ひらがな・カタカナ・漢字を含む行だけを保持
        if re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", line_clean):
            # 英語の前置きが付いている場合はカット
            line_clean = re.sub(r"^(Something like:|In Japanese:|\* )\s*", "", line_clean, flags=re.IGNORECASE)
            japanese_lines.append(line_clean)
            
    result = " ".join(japanese_lines).strip()
    return result if result else "意見なし"

def generate_response(system_instruction, prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_instruction,
        "stream": False,
        "options": {
            "temperature": 0.5,
            "top_p": 0.9
        }
    }
    try:
        res = requests.post(OLLAMA_URL, json=payload)
        raw_text = res.json().get("response", "").strip()
        return clean_text(raw_text)
    except Exception as e:
        return f"[エラー: {e}]"

def run_discussion():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(OUTPUT_DIR, f"{today_str}_Discussion_Log.md")
    
    log_content = f"# AI社員 検討会議ログ\n日付: {today_str}\n\n## 議題\n{TOPIC}\n\n---\n\n## 発言ログ\n\n"
    print(f"=== 議題: {TOPIC} ===")

    discussion_history = f"議題: {TOPIC}\n"

    system_instruction = "あなたは社内会議の参加者です。思考過程・英語・挨拶は一切出力せず、日本語の結論と発言のみを1文〜2文で端的に述べてください。"

    for m in MEMBERS:
        prompt = f"""役職: {m['name']}
立場: {m['role']}

これまでの流れ:
{discussion_history}

上記の議題に対し、あなたの立場から結論と理由を日本語で簡潔に述べてください。"""

        print(f"\n[{m['name']}] が発言中...")
        comment = generate_response(system_instruction, prompt)
        print(f"{m['name']}: {comment}")
        
        entry = f"### {m['name']}\n> {comment}\n\n"
        log_content += entry
        discussion_history += f"{m['name']}: {comment}\n"

    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(log_content)

    print(f"\n日本語ログを保存しました: {output_path}")

if __name__ == "__main__":
    run_discussion()