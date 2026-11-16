---
title: "Jev 監査・自己改善ダッシュボード"
date: 2026-11-16
updated: 2026-11-16 12:29:02
type: dashboard
tags:
  - dashboard/jev
  - property_management
---

# 🛡️ Jev 監査・トリアージ対応ダッシュボード

> 最終自動更新: `2026-11-16 12:29:02` ｜ 監査モデル: `ornith-9b:latest`

[▶ メール巡回＆Jev監査バッチを実行 (run_triage_loop.bat)](file:///G:/マイドライブ/Obsidian_2/antigravity-Jev-demo/run_triage_loop.bat)

---

## 📊 監査サマリ

| 全体レポート数 | 合格 (PASS) | 不合格 (FAIL) | 平均承認スコア |
| :---: | :---: | :---: | :---: |
| **11 件** | <font color="#2da2bb">**11 件**</font> | <font color="#fb4c2f">**0 件**</font> | **0.92** |

- 🧬 **3層ハイブリッドJev監査**: 2 件
- 🚨 **着信メールトリアージ**: 3 件
- ⛄ **北海道・冬期凍結＆給湯器**: 3 件
- 🔇 **騒音・生活マナー苦情**: 1 件
- 🏠 **入居者問い合わせ対応**: 1 件
- 💻 **コード品質自己修復**: 1 件

---

## ⚠️ 要確認・複数回推敲レポート（試行 2回以上 または FAIL）
> Jevの指摘により安全措置や免責条項が自己修復された重要履歴です。

| レポート名 | 実行日時 | 判定 | 仕分けレーン | 試行回数 | スコア |
| :--- | :--- | :---: | :---: | :---: | :---: |
| [Winter_Freeze_Report_20261116_122902](../06_Reports/Winter_Freeze_Report_20261116_122902.md) | 2026-11-16 12:29:02 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.95` |
| [Winter_Freeze_Report_20261106_065325](../06_Reports/Winter_Freeze_Report_20261106_065325.md) | 2026-11-06 06:53:25 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.95` |
| [Triage_Audit_20261105_220551](../06_Reports/Triage_Audit_20261105_220551.md) | 2026-11-05 22:05:51 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.95` |
| [Triage_Audit_20261105_213807](../06_Reports/Triage_Audit_20261105_213807.md) | 2026-11-05 21:38:07 | ✅ PASS | 🚀 標準PASS | **3 回** | `0.92` |
| [Triage_Audit_20261105_211859](../06_Reports/Triage_Audit_20261105_211859.md) | 2026-11-05 21:18:59 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.92` |
| [Tenant_Reply_Report_20261105_210253](../06_Reports/Tenant_Reply_Report_20261105_210253.md) | 2026-11-05 21:02:53 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.96` |
| [Noise_Triage_Report_20261106_080835](../06_Reports/Noise_Triage_Report_20261106_080835.md) | 2026-11-06 08:08:35 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.9` |
| [Jev_Report_20261105_174308](../06_Reports/Jev_Report_20261105_174308.md) | 2026-11-05 17:43:08 | ✅ PASS | 🚀 標準PASS | **2 回** | `1.0` |
| [Hybrid_Audit_20261107_053310](../06_Reports/Hybrid_Audit_20261107_053310.md) | 2026-11-07 05:33:10 | ✅ PASS | [⚠️要よっちゃん確認] | 1 回 | `0.64` |
| [Audit_winter_freeze_triage_20261106_083131](../06_Reports/Audit_winter_freeze_triage_20261106_083131.md) | 2026-11-06 08:31:31 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.95` |


---

## 🧬 0. 3層ハイブリッドJev監査（二値×段階×確率 / `hybrid_jev`）

| レポート名 | 実行日時 | 判定 | 仕分けレーン | 試行回数 | スコア |
| :--- | :--- | :---: | :---: | :---: | :---: |
| [Hybrid_Audit_20261107_053310](../06_Reports/Hybrid_Audit_20261107_053310.md) | 2026-11-07 05:33:10 | ✅ PASS | [⚠️要よっちゃん確認] | 1 回 | `0.64` |
| [Hybrid_Audit_20261106_210706](../06_Reports/Hybrid_Audit_20261106_210706.md) | 2026-11-06 21:07:06 | ✅ PASS | 🚀 標準PASS | 1 回 | `0.93` |


---

## ⛄ 1. 北海道・冬期凍結＆給湯器トラブル 監査 (`winter_freeze_triage`)

| レポート名 | 実行日時 | 判定 | 仕分けレーン | 試行回数 | スコア |
| :--- | :--- | :---: | :---: | :---: | :---: |
| [Winter_Freeze_Report_20261116_122902](../06_Reports/Winter_Freeze_Report_20261116_122902.md) | 2026-11-16 12:29:02 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.95` |
| [Winter_Freeze_Report_20261106_065325](../06_Reports/Winter_Freeze_Report_20261106_065325.md) | 2026-11-06 06:53:25 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.95` |
| [Audit_winter_freeze_triage_20261106_083131](../06_Reports/Audit_winter_freeze_triage_20261106_083131.md) | 2026-11-06 08:31:31 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.95` |


---

## 🔇 2. 騒音・生活マナー苦情対応 監査 (`noise_triage`)

| レポート名 | 実行日時 | 判定 | 仕分けレーン | 試行回数 | スコア |
| :--- | :--- | :---: | :---: | :---: | :---: |
| [Noise_Triage_Report_20261106_080835](../06_Reports/Noise_Triage_Report_20261106_080835.md) | 2026-11-06 08:08:35 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.9` |


---

## 🚨 3. 着信メール トリアージ＆Jev監査 (`mail_triage_concierge`)

| レポート名 | 実行日時 | 判定 | 仕分けレーン | 試行回数 | スコア |
| :--- | :--- | :---: | :---: | :---: | :---: |
| [Triage_Audit_20261105_220551](../06_Reports/Triage_Audit_20261105_220551.md) | 2026-11-05 22:05:51 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.95` |
| [Triage_Audit_20261105_213807](../06_Reports/Triage_Audit_20261105_213807.md) | 2026-11-05 21:38:07 | ✅ PASS | 🚀 標準PASS | **3 回** | `0.92` |
| [Triage_Audit_20261105_211859](../06_Reports/Triage_Audit_20261105_211859.md) | 2026-11-05 21:18:59 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.92` |


---

## 🏠 4. 入居者問い合わせ対応文 監査 (`tenant_inquiry`)

| レポート名 | 実行日時 | 判定 | 仕分けレーン | 試行回数 | スコア |
| :--- | :--- | :---: | :---: | :---: | :---: |
| [Tenant_Reply_Report_20261105_210253](../06_Reports/Tenant_Reply_Report_20261105_210253.md) | 2026-11-05 21:02:53 | ✅ PASS | 🚀 標準PASS | **2 回** | `0.96` |


---

## 💻 5. コード品質・自己修復 監査 (`code_eval`)

| レポート名 | 実行日時 | 判定 | 仕分けレーン | 試行回数 | スコア |
| :--- | :--- | :---: | :---: | :---: | :---: |
| [Jev_Report_20261105_174308](../06_Reports/Jev_Report_20261105_174308.md) | 2026-11-05 17:43:08 | ✅ PASS | 🚀 標準PASS | **2 回** | `1.0` |


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
