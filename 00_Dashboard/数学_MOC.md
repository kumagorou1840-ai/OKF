---
created: 2026-11-15
type: moc
---

# 数学_MOC

## 紐づくGoogleドキュメント・PDF一覧（自動集約）
```dataview
TABLE WITHOUT ID
  "[[" + file.name + "|📝カード]]" AS "詳細",
  "[🔗 " + file.name + "](" + gdoc_url + ")" AS "Googleドライブ",
  summary AS "要約",
  filter(links, (x) => x != this.file.link) AS "他の関連テーマ",
  dateformat(file.ctime, "yyyy-MM-dd") AS "登録日"
FROM "03_Resources/GDoc_Cards"
WHERE type = "gdoc-card" AND contains(links, this.file.link)
SORT file.ctime DESC
```

## 思考メモ・全体方針
- 
