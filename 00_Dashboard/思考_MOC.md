---
created: 2026-11-15
type: moc
---

# 思考_MOC

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

## 思考メモ・全体方針
- ループ #Notebook #AIエージェント#youtube
- python -c "import sys; sys.path.append(r'C:\Users\PC_User\Obsidian_2\scripts'); from gdoc_card_generator import *; Obsidian2CardManager(VAULT_ROOT, CARDS_OUTPUT_DIR, MOC_OUTPUT_DIR).process_file(Path(r'G:\マイドライブ\MOC\思考\ループ.gdoc'))"
- $f = Get-ChildItem "G:\マイドライブ\MOC" -Recurse -Filter "*ループ*" | Select-Object -First 1; if ($f) { "発見: $($f.FullName)"; python -c "import sys; sys.path.append(r'C:\Users\PC_User\Obsidian_2\scripts'); from gdoc_card_generator import *; Obsidian2CardManager(VAULT_ROOT, CARDS_OUTPUT_DIR, MOC_OUTPUT_DIR).process_file(Path(r'$($f.FullName)'))" } else { "Gドライブ上にまだ同期されていません" }
- 画面に **`発見: G:\マイドライブ\MOC\...`** と **`[SUCCESS] 中継カード生成`** が出れば完了です！
