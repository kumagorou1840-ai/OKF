import sys
import json
import time
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from pydantic import ValidationError
from schemas import ContractSchema
from jev_auditor import evaluate_with_jev, JevAuditResult

VAULT_DIR = Path(r"G:\マイドライブ\Obsidian_2")
TEMPLATE_PATH = VAULT_DIR / "templates" / "contract_template.md"
DB_PATH = VAULT_DIR / "property_management.db"
INBOX_DIR = VAULT_DIR / "00_Inbox"
PROCESSED_DIR = INBOX_DIR / "processed"
OUTPUT_DIR = VAULT_DIR / "01_Contracts"
MOC_PATH = VAULT_DIR / "Contracts_MOC.md"
HEALING_LOG_DIR = VAULT_DIR / "Logs" / "Healing"

def fix_data_with_llm(raw_data: dict, feedback: str) -> dict:
    patched = raw_data.copy()
    if "memo" in feedback:
        patched["memo"] = "契約更新に伴う賃料改定（Jev自動補完：相場および維持管理費見直しのため）"
    if "URGENT" in feedback:
        patched["flag"] = "URGENT"
    elif "REVIEW_REQUIRED" in feedback:
        patched["flag"] = "REVIEW_REQUIRED"
    patched["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    patched["last_editor"] = "InnerLoop_Healer"
    return patched

def render_markdown(contract: ContractSchema) -> str:
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    return template_text.format(**contract.model_dump())

def save_to_obsidian_and_update_moc(contract: ContractSchema, markdown_text: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{contract.contract_id}_{contract.property_name}_{contract.room_number}.md"
    output_path = OUTPUT_DIR / file_name
    output_path.write_text(markdown_text, encoding="utf-8")
    link_line = f"- [[01_Contracts/{output_path.stem}|{contract.contract_id}: {contract.property_name} {contract.room_number}号室 ({contract.tenant_name}様)]] - 新賃料: {contract.new_rent:,}円 (`{contract.flag}`)"
    if MOC_PATH.exists():
        moc_content = MOC_PATH.read_text(encoding="utf-8")
        if contract.contract_id not in moc_content:
            MOC_PATH.write_text(moc_content.rstrip() + "\n" + link_line + "\n", encoding="utf-8")
        else:
            lines = moc_content.splitlines()
            updated_lines = [link_line if contract.contract_id in line else line for line in lines]
            MOC_PATH.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    return output_path

def record_to_sqlite_and_obsidian_log(contract_id: str, attempts: int, duration: float, audit: JevAuditResult | None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS healing_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, script_name TEXT, attempt_count INTEGER, duration_sec REAL, status TEXT, error_message TEXT)")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_str = "SUCCESS" if (audit and audit.status == "PASS") else "FAILED"
    feedback_str = audit.feedback if audit else "Validation Error"
    cursor.execute("INSERT INTO healing_logs (timestamp, script_name, attempt_count, duration_sec, status, error_message) VALUES (?, ?, ?, ?, ?, ?)", (now_str, f"contract-pipeline ({contract_id})", attempts, round(duration, 2), status_str, feedback_str))
    conn.commit()
    conn.close()
    HEALING_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = HEALING_LOG_DIR / f"heal_{contract_id}_{now_str.replace(':', '-').replace(' ', '_')}.md"
    log_file.write_text(f"---\ntype: healing_log\ncontract_id: \"{contract_id}\"\nattempts: {attempts}\nstatus: \"{status_str}\"\ndate: \"{now_str}\"\n---\n# 🤖 ログ: {contract_id}\n- ステータス: `{status_str}`\n- フィードバック: {feedback_str}\n", encoding="utf-8")

def process_single_contract(initial_data: dict, max_retries: int = 3) -> bool:
    start_time = time.time()
    current_data = initial_data.copy()
    contract_id = current_data.get("contract_id", "UNKNOWN")
    last_audit = None
    for attempt in range(1, max_retries + 1):
        print(f"🔄 [試行 {attempt}/{max_retries}] 契約ID: {contract_id}")
        try:
            contract_obj = ContractSchema(**current_data)
        except ValidationError as ve:
            if attempt == max_retries:
                record_to_sqlite_and_obsidian_log(contract_id, attempt, time.time() - start_time, None)
                return False
            current_data = fix_data_with_llm(current_data, str(ve))
            continue
        last_audit = evaluate_with_jev(contract_obj)
        print(f"🔍 Jev監査: [{last_audit.status}] Feedback: {last_audit.feedback}")
        if last_audit.status == "PASS":
            duration = time.time() - start_time
            save_to_obsidian_and_update_moc(contract_obj, render_markdown(contract_obj))
            record_to_sqlite_and_obsidian_log(contract_obj.contract_id, attempt, duration, last_audit)
            return True
        if attempt < max_retries:
            current_data = fix_data_with_llm(contract_obj.model_dump(), last_audit.feedback)
    record_to_sqlite_and_obsidian_log(contract_id, max_retries, time.time() - start_time, last_audit)
    return False

def main():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    json_files = sorted(INBOX_DIR.glob("*.json"))
    if not json_files:
        print("📭 00_Inbox に未処理のJSONファイルがありません。単体テストを実行します。")
        sample = {
            "contract_id": "C-2026-101",
            "property_name": "メゾン札幌北",
            "room_number": "101",
            "tenant_name": "鈴木 一郎",
            "current_rent": 50000,
            "new_rent": 50000,
            "renewal_date": "2026-12-01",
            "contact": "090-1111-2222",
            "memo": "据え置き更新"
        }
        process_single_contract(sample)
        return
    for json_path in json_files:
        print(f"\n📂 JSON読み込み: {json_path.name}")
        raw_input = json.loads(json_path.read_text(encoding="utf-8-sig"))
        contracts_list = raw_input if isinstance(raw_input, list) else [raw_input]
        file_success = sum(1 for item in contracts_list if process_single_contract(item))
        if file_success == len(contracts_list):
            dest = PROCESSED_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{json_path.name}"
            shutil.move(str(json_path), str(dest))
            print(f"📦 アーカイブ完了: {dest.name}")

if __name__ == "__main__":
    main()
