# アーキテクチャ決定記録（ADR）一覧

```dataview
TABLE 状態 AS "状態", 評価軸 AS "重視した評価軸", 決定者 AS "決定者", 作成日 AS "作成日"
FROM #architecture/adr
WHERE file.name != "ADR一覧"
SORT file.name ASC
```

---

### 週次・月次レビュー用：評価軸の出現パターン

```dataview
TABLE length(rows) AS "件数", rows.file.link AS "関連ADR"
FROM #architecture/adr
WHERE file.name != "ADR一覧" AND 評価軸
FLATTEN 評価軸 AS 軸
GROUP BY 軸
SORT length(rows) DESC
```