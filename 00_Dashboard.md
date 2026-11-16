# WikiSkill Evolution Dashboard

## 🚨 未解決の重要パターン（Activeのみ / 最大5件）
```dataview
TABLE type, detected_iteration
FROM "wiki/patterns"
WHERE status = "active"
SORT file.name desc
LIMIT 5
```

## 📋 最新のパターン履歴（直近10件）
```dataview
TABLE type, status, detected_iteration
FROM "wiki/patterns"
SORT file.name desc
LIMIT 10
```

## 採択されたスキル更新
```dataview
TABLE version, updated, description
FROM "skills"
WHERE file.name = "SKILL"
SORT updated desc
```
