from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "report_template.md"
OUTPUT_DIR = BASE_DIR.parent.parent.parent / "reports"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    content = (
        template.replace("{{DATE}}", today)
        .replace("{{TITLE}}", f"{today} 自動生成レポート")
        .replace("{{CATEGORY}}", "General Report")
    )
    output_path = OUTPUT_DIR / f"{today}_report.md"
    output_path.write_text(content, encoding="utf-8")
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    main()
