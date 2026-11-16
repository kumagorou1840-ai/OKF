from datetime import datetime
from pathlib import Path

def generate_report(data: dict, output_filename: str = None):
    # パスの基準設定（スクリプトの位置を基準にする場合）
    script_dir = Path(__file__).resolve().parent
    skill_dir = script_dir.parent
    
    template_path = skill_dir / "templates" / "report_template.md"
    
    # 出力先（プロジェクトの 06_Reports フォルダ等を想定）
    project_root = skill_dir.parent.parent
    reports_dir = project_root / "06_Reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    if not output_filename:
        output_filename = f"{datetime.now().strftime('%Y-%m-%d')}_report.md"
    
    output_path = reports_dir / output_filename
    
    # 1. テンプレートの読み込み
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    content = template_path.read_text(encoding="utf-8")
    
    # 2. 変数の置換（{{key}} を value に置換）
    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        content = content.replace(placeholder, str(value))
        
    # 3. ファイル出力
    output_path.write_text(content, encoding="utf-8")
    print(f"Report successfully generated at: {output_path}")

if __name__ == "__main__":
    # 埋め込むデータのサンプル
    sample_data = {
        "title": "月次運用レポート",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source_name": "triage_log.db",
        "metric_1": "入居率",
        "value_1": "95.5%",
        "diff_1": "+1.2%"
    }
    generate_report(sample_data)