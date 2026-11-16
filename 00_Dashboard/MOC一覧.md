---
created: 2026-11-15
type: master-index
---

# MOCマスターインデックス（全テーマ一覧）

## 自動生成されたテーマ目次（*_MOC）
```dataview
TABLE WITHOUT ID
  "[[" + file.name + "|📁 " + replace(file.name, "_MOC", "") + "]]" AS "テーマ",
  length(file.inlinks) AS "紐づくカード数",
  dateformat(file.mtime, "yyyy-MM-dd") AS "最終更新日"
FROM "00_Dashboard"
WHERE endswith(file.name, "_MOC")
SORT length(file.inlinks) DESC, file.name ASC
```


## 最新のGoogleドキュメント登録履歴（直近20件）
```dataview
TABLE WITHOUT ID
  "[[" + file.name + "|📝 " + file.name + "]]" AS "カード",
  links AS "所属テーマ",
  "[🔗 開く](" + gdoc_url + ")" AS "Gドライブ",
  dateformat(file.ctime, "yyyy-MM-dd HH:mm") AS "登録日時"
FROM "03_Resources/GDoc_Cards"
WHERE type = "gdoc-card"
SORT file.ctime DESC
LIMIT 20
```

