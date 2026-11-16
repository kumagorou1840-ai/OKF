import os
import re
import glob

VAULT_DIR = r"C:\Users\PC_User\Documents\Obsidian\obsidian_2"
SUMMARIES_DIR = os.path.join(VAULT_DIR, "03_Resources", "YouTube_Summaries")
TASKS_DIR = os.path.join(VAULT_DIR, "01_Tasks")
COCKPIT_MOC_PATH = os.path.join(VAULT_DIR, "00_Dashboard", "Cockpit_MOC.md")

def sanitize_filename(name):
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    return cleaned.strip().replace(" ", "_")

def process_summaries():
    summary_files = glob.glob(os.path.join(SUMMARIES_DIR, "*.md"))
    if not summary_files:
        print(f"No summary files found in {SUMMARIES_DIR}")
        return

    extracted_tasks = []

    for filepath in summary_files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        doc_title = title_match.group(1).strip() if title_match else os.path.basename(filepath).replace(".md", "")
        
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        task_filename = f"Task_YT_{sanitize_filename(base_name)}.md"
        task_filepath = os.path.join(TASKS_DIR, task_filename)

        tasks = re.findall(r"^\s*-\s*\[\s*\]\s+(.+)$", content, re.MULTILINE)
        
        knowledge_match = re.search(r"##\s+💡\s*重要な知見[^\n]*\n([\s\S]*?)(?=\n##|\Z)", content)
        knowledge_text = knowledge_match.group(1).strip() if knowledge_match else ""

        if tasks:
            task_content = f"""---
tags:
  - task/youtube
  - status/backlog
source_note: "[[{os.path.basename(filepath)}]]"
created: 2026-10-03
---

# 📋 {doc_title} からの抽出タスク

## 🔗 元ノート
- [[{os.path.basename(filepath)}]]

## 💡 ピックアップナレッジ
{knowledge_text if knowledge_text else "- ナレッジ自動抽出済み"}

## 📝 実務アクションタスク (TODO)
"""
            for t in tasks:
                task_content += f"- [ ] {t}\n"

            with open(task_filepath, "w", encoding="utf-8") as tf:
                tf.write(task_content)
            print(f"Created task note: {task_filename}")

            extracted_tasks.append({
                "filename": task_filename,
                "title": doc_title,
                "task_count": len(tasks)
            })

    # Update Cockpit_MOC.md
    if extracted_tasks and os.path.exists(COCKPIT_MOC_PATH):
        with open(COCKPIT_MOC_PATH, "r", encoding="utf-8") as mf:
            moc_content = mf.read()

        updated = False
        for task_info in extracted_tasks:
            link_entry = f"- [ ] [{task_info['filename']}](../01_Tasks/{task_info['filename']}) - {task_info['title']} ({task_info['task_count']}件)"
            if task_info['filename'] not in moc_content:
                target_heading = "### ⏳ 未着手 (Backlog)"
                if target_heading in moc_content:
                    moc_content = moc_content.replace(target_heading, f"{target_heading}\n{link_entry}")
                    updated = True
                    print(f"Added to Cockpit_MOC: {task_info['filename']}")

        if updated:
            with open(COCKPIT_MOC_PATH, "w", encoding="utf-8") as mf:
                mf.write(moc_content)
            print("Cockpit_MOC.md successfully updated!")

if __name__ == "__main__":
    process_summaries()
