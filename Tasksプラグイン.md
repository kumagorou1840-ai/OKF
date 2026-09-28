ObsidianのTasksプラグインにおける主要なフィルター構文の書き方一覧です。

  

|**分類**|**構文例**|**説明**|
|---|---|---|
|**完了状態**|`not done`|未完了のタスクのみ抽出|
||`done`|完了済みのタスクのみ抽出|
|**期日（Due）**|`due before in 3 weeks`|今日から3週間後より前の期日|
||`due in or before 3 weeks`|3週間後当日を含む、それ以前の期日|
||`due today`|期日が今日のもの|
||`due before tomorrow`|期日が今日以前のもの（期限切れ＋今日）|
||`no due date`|期日が設定されていないタスク|
|**重要度（Priority）**|`priority is high`|重要度が「高（🔺）」のみ|
||`priority is highest`|重要度が「最高（⏫）」のみ|
||`priority above medium`|重要度が「中」より上（高・最高）|
||`priority is not none`|重要度が設定されているもの全て|
|**並び替え（Sort）**|`sort by due`|期日が近い順に並び替え|
||`sort by priority`|重要度が高い順に並び替え|
|**表示制限**|`limit 10`|表示件数を最大10件に制限|

**組み合わせ例（3週間以内の高優先度タスクを期日順に表示）**

  

Markdown

````
```tasks
not done
due in or before 3 weeks
priority above medium
sort by due
sort by priority
```
````

用途に合わせて組み合わせを変えてご利用ください。