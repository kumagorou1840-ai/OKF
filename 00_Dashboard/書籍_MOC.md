---
created: 2026-11-15
type: moc
---

# 書籍_MOC

## 紐づくGoogleドキュメント一覧（自動集約）
```dataview
TABLE WITHOUT ID
  "[[" + file.name + "|📝カード]]" AS "詳細",
  "[🔗 " + file.name + "](" + gdoc_url + ")" AS "Googleドキュメント",
  summary AS "要約",
  filter(links, (x) => x != this.file.link) AS "他の関連テーマ",
  dateformat(file.ctime, "yyyy-MM-dd") AS "登録日"
FROM "03_Resources/GDoc_Cards"
WHERE type = "gdoc-card" AND contains(links, this.file.link)
SORT file.ctime DESC
```

## 書籍メモ・全体方針

- G:\マイドライブ\MOC\書籍\黄金比_1 #数学 #GoogleColab.pdf
- ファイル名：黄金比_1 #数学 #GoogleColab.pdf
- リンク:#数学 #GoogleColab
- PowerShellで入力する場合:

```
python -c "import sys; sys.path.append(r'C:\Users\PC_User\Obsidian_2\scripts'); from gdoc_card_generator import *; Obsidian2CardManager(VAULT_ROOT, CARDS_OUTPUT_DIR, MOC_OUTPUT_DIR).process_file(Path(r'G:\マイドライブ\MOC\書籍\黄金比_1 #数学 #GoogleColab.pdf'))"
```

画面に **`[SUCCESS] 中継カード生成 (.pdf): 黄金比_1.md -> ['"[[書籍_MOC]]"', '"[[数学_MOC]]"', '"[[GoogleColab_MOC]]"']`** と表示されたら完了です！結果をお知らせください。

