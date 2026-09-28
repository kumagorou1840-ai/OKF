[[No.160_戦略SWOT分析ジェネレーター]]

obsidianと外部のdataとのlink方法は？

Obsidianと外部データをリンク（連携・参照・埋め込み）する方法は、「参照（リンク）」「埋め込み・表示」「データ取得（プラグイン）」の3つのアプローチに大別されます。

### 1. 標準Markdownリンク（ローカルファイル・Webリンク）

もっとも軽量かつ標準的な方法です。

- **ローカルファイルへの絶対パスリンク (`file:///`)** PC内のExcel、PDF、ローカルHTMLなどを直接クリックして既定のアプリで開きます。
    
    Markdown
    
    ```
    [売上集計.xlsx](file:///C:/Users/PC_User/Documents/Data/sales.xlsx)
    [ダッシュボード](file:///C:/Users/PC_User/Desktop/dashboard.html)
    ```
    
    _(※空白を含むパスは `%20` に置換するか、`<file:///...>` で囲みます)_
    
- **Web URLリンク** Web上のダッシュボードやAPIドキュメント、Googleスプレッドシートへの直接リンクです。
    
    Markdown
    
    ```
    [スキル活用ナビゲーター Pro](https://example.com/navigator)
    ```
    

### 2. インライン埋め込み（PDF・画像・iframe）

Obsidianノートの閲覧画面内に外部コンテンツをそのまま表示します。

- **ローカルファイル・PDFのプレビュー** `!` を先頭に付けることでノート内に直接レンダリングされます。
    
    Markdown
    
    ```
    ![[C:/Users/PC_User/Documents/report.pdf]]
    ```
    
- **iframeによるWebアプリ・HTML埋め込み** HTML5ダッシュボードやWebアプリをObsidianの画面内でそのまま操作できます。
    
    HTML
    
    ```
    <iframe src="http://localhost:8050" width="100%" height="600px" frameborder="0"></iframe>
    ```
    

### 3. コミュニティプラグインによるデータ連携

外部データを取り込み、Obsidian内で動的に活用する手法です。

|プラグイン名|連携対象・機能|主な活用例|
|---|---|---|
|**Dataview**|ノート内のフロントマター（YAML）やタグ|散在するタスクノートから一覧表やKPIテーブルを動的生成|
|**Obsidian URL (標準機能)**|外部アプリ → Obsidian への逆リンク|ブラウザやPythonスクリプトから特定ノートを直接開く (`obsidian://open?...`)|
|**JSON / CSV Importer**|CSV, JSON ファイル|外部出力データをObsidianのノート群へ一括変換・同期|
|**Database Folder**|ノート群をNotion風テーブル化|プロンプト一覧やデータ分析タスクのステータス管理|

特定のデータ形式（例: SQLite、CSV、Pythonスクリプト、WebAPI）との具体的な接続コードや設定例が必要な場合は、対象のデータをお知らせください。
