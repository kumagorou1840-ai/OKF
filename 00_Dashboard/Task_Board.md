# 📋 Task Board（タスク一元管理ボード）

## ⏳ 進行中・未完了タスク
```dataview
TASK
FROM "01_Tasks" OR "07_Ideas"
WHERE !completed
GROUP BY file.name
```





