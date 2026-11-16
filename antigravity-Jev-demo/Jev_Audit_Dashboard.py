import os
import re
from pathlib import Path
from datetime import datetime

VAULT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = VAULT_ROOT / "06_Reports"
DASHBOARD_FILE = VAULT_ROOT / "00_Dashboard" / "Jev_Audit_Dashboard.md"


def parse_frontmatter(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    meta = {"file_name": md_path.stem, "file_path": f"06_Reports/{md_path.name}"}
    for line in match.group(1).splitlines():
        if ":" in line and not line.strip().startswith("-"):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta


def build_dashboard():
    reports = []
    for md_file in sorted(REPORTS_DIR.glob("*.md"), reverse=True):
        meta = parse_frontmatter(md_file)
        if meta.get("type") == "eval_report":
            reports.append(meta)

    total = len(reports)
    pass_count = sum(1 for r in reports if r.get("status") == "PASS")
    fail_count = sum(1 for r in reports if r.get("status") == "FAIL")
    scores = [float(r.get("score", 0.0)) for r in reports if r.get("score")]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    # カテゴリ別
    hybrid_list = [r for r in reports if r.get("category") == "hybrid_jev"]
    triage_list = [r for r in reports if r.get("category") == "mail_triage_concierge"]
    winter_list = [r for r in reports if r.get("category") == "winter_freeze_triage"]
    noise_list = [r for r in reports if r.get("category") == "noise_triage"]
    tenant_list = [r for r in reports if r.get("category") == "tenant_inquiry"]
    code_list = [r for r in reports if not r.get("category")]

    # 要警戒・複数回試行案件（試行2回以上、HUMAN_REVIEW/AUTO_REJECT、またはFAIL）
    caution_list = [
        r for r in reports
        if int(r.get("attempts", 1)) >= 2
        or r.get("status") == "FAIL"
        or r.get("action_lane") in ("HUMAN_REVIEW", "AUTO_REJECT")
    ]

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = datetime.now().strftime("%Y-%m-%d")

    def make_table(items: list) -> str:
        if not items:
            return "_該当するレポートはありません。_\n"
        lines = [
            "| レポート名 | 実行日時 | 判定 | 仕分けレーン | 試行回数 | スコア |",
            "| :--- | :--- | :---: | :---: | :---: | :---: |",
        ]
        for r in items:
            link = f"[{r['file_name']}](../{r['file_path']})"
            date_val = r.get("date", "-")
            status_val = "✅ PASS" if r.get("status") == "PASS" else f"❌ {r.get('status', '-')}"
            lane_val = r.get("draft_prefix") or r.get("action_lane") or "🚀 標準PASS"
            attempts_val = f"**{r.get('attempts', '-')} 回**" if int(r.get("attempts", 1)) > 1 else f"{r.get('attempts', '-')} 回"
            score_val = f"`{r.get('score', '-')}`"
            lines.append(f"| {link} | {date_val} | {status_val} | {lane_val} | {attempts_val} | {score_val} |")
        return "\n".join(lines) + "\n"

    md_content = f"""---
title: "Jev 監査・自己改善ダッシュボード"
date: {today_str}
updated: {now_str}
type: dashboard
tags:
  - dashboard/jev
  - property_management
---

# 🛡️ Jev 監査・トリアージ対応ダッシュボード

> 最終自動更新: `{now_str}` ｜ 監査モデル: `ornith-9b:latest`

[▶ メール巡回＆Jev監査バッチを実行 (run_triage_loop.bat)](file:///G:/マイドライブ/Obsidian_2/antigravity-Jev-demo/run_triage_loop.bat)

---

## 📊 監査サマリ

| 全体レポート数 | 合格 (PASS) | 不合格 (FAIL) | 平均承認スコア |
| :---: | :---: | :---: | :---: |
| **{total} 件** | <font color="#2da2bb">**{pass_count} 件**</font> | <font color="#fb4c2f">**{fail_count} 件**</font> | **{avg_score}** |

- 🧬 **3層ハイブリッドJev監査**: {len(hybrid_list)} 件
- 🚨 **着信メールトリアージ**: {len(triage_list)} 件
- ⛄ **北海道・冬期凍結＆給湯器**: {len(winter_list)} 件
- 🔇 **騒音・生活マナー苦情**: {len(noise_list)} 件
- 🏠 **入居者問い合わせ対応**: {len(tenant_list)} 件
- 💻 **コード品質自己修復**: {len(code_list)} 件

---

## ⚠️ 要確認・複数回推敲レポート（試行 2回以上 または FAIL）
> Jevの指摘により安全措置や免責条項が自己修復された重要履歴です。

{make_table(caution_list)}

---

## 🧬 0. 3層ハイブリッドJev監査（二値×段階×確率 / `hybrid_jev`）

{make_table(hybrid_list)}

---

## ⛄ 1. 北海道・冬期凍結＆給湯器トラブル 監査 (`winter_freeze_triage`)

{make_table(winter_list)}

---

## 🔇 2. 騒音・生活マナー苦情対応 監査 (`noise_triage`)

{make_table(noise_list)}

---

## 🚨 3. 着信メール トリアージ＆Jev監査 (`mail_triage_concierge`)

{make_table(triage_list)}

---

## 🏠 4. 入居者問い合わせ対応文 監査 (`tenant_inquiry`)

{make_table(tenant_list)}

---

## 💻 5. コード品質・自己修復 監査 (`code_eval`)

{make_table(code_list)}

---

## 🔄 Dataview 動的集計ビュー

```dataview
TABLE WITHOUT ID
  file.link AS "レポート",
  choice(category = "winter_freeze_triage", "⛄ 冬期凍結", choice(category = "noise_triage", "🔇 騒音苦情", choice(category = "mail_triage_concierge", "🚨 メールトリアージ", choice(category = "tenant_inquiry", "🏠 入居者対応", "💻 コード評価")))) AS "区分",
  status AS "判定",
  attempts + "回" AS "試行",
  score AS "スコア",
  date AS "受付日時"
FROM "06_Reports"
WHERE type = "eval_report"
SORT date DESC
```
"""

    DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_FILE.write_text(md_content, encoding="utf-8")

    print("=== [Jev Audit Dashboard 集計完了] ===")
    print(f"・総監査レポート数: {total} 件 (PASS: {pass_count} / FAIL: {fail_count})")
    print(f"・平均承認スコア  : {avg_score}")
    print(f"  - ⚠️ 要確認・複数回推敲: {len(caution_list)} 件")
    print(f"  - 🧬 3層ハイブリッド監査: {len(hybrid_list)} 件")
    print(f"  - ⛄ 冬期凍結・給湯器  : {len(winter_list)} 件")
    print(f"  - 🔇 騒音・マナー苦情  : {len(noise_list)} 件")
    print(f"  - 🚨 着信メールトリアージ: {len(triage_list)} 件")
    print(f"  - 🏠 入居者問い合わせ対応: {len(tenant_list)} 件")
    print(f"  - 💻 コード品質自己修復: {len(code_list)} 件")
    print(f"=> ダッシュボードを更新しました: {DASHBOARD_FILE}")


if __name__ == "__main__":
    build_dashboard()
