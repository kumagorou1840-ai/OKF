---
type: ナレッジ仕様書
title: PlantUML 非UML・データ可視化仕様ガイド (OKFモジュール)
category: ソフトウェア開発 / データ構造 / 業務フロー可視化
tags: [PlantUML, JSON, YAML, nwdiag, Salt, Wireframe, MindMap, WBS, Gantt, ER, OKF]
created_at: 2026-07-27
updated_at: 2026-07-27
---

# PlantUML 非UML・データ可視化仕様ガイド (OKFモジュール)

---

## 📋 1. 前提情報 (選択能力・メタデータ)

| 項目 | 内容 |
| :--- | :--- |
| **領域** | データ表現・プロジェクト管理・ワイヤーフレーム領域 |
| **タイトル** | PlantUML 非UML・データ可視化仕様ガイド |
| **できること** | JSON/YAMLのビジュアルツリー化、ネットワーク構成図 (nwdiag)、GUIワイヤーフレーム (Salt)、MindMap、WBS、ガントチャート、ER図のコード生成 |
| **実例** | APIレスポンスデータ構造のツリー可視化、インフラネットワーク構成図の自動レンダリング、画面レイアウトのテキストプロトタイピング |
| **リソース** | PlantUML Language Reference Guide (pp.276 - 470) |
| **関連ドキュメント** | [PlantUML言語リファレンス メイン](file:///C:/Users/PC_User/OKF/plantuml_language_reference.md) \| [PlantUML UMLダイアグラム仕様](file:///C:/Users/PC_User/OKF/plantuml_uml_diagrams.md) \| [PlantUML スタイル・プリプロセッサ仕様](file:///C:/Users/PC_User/OKF/plantuml_styling_and_preprocessor.md) |
| **全体目次** | [OKFナレッジインデックス (INDEX.md)](file:///C:/Users/PC_User/OKF/INDEX.md) |

---

## 🔬 2. よっちゃん流ハイブリッド診断 (分析＆未来ベクトル)

### 🧠 Karpathy流「8つの視点」による評価
- **Software 1.0/2.0/3.0 の共存**: テキスト仕様(1.0) + リッチダイアグラム自動生成(2.0) + AIによる要件定義書からのWBS/MindMap/画面ワイヤーフレーム自動起稿(3.0)。
- **Build for Agents**: JSON/YAMLやインフラ構成、画面レイアウトをエージェントがテキストコードで出力し、人間と即座に画面レビューを行うための基盤。

---

## 📖 3. 非UML・データ可視化 詳細仕様 & 構文リファレンス

### 3.1 JSON / YAML データ構造可視化

#### JSON 可視化 (`@startjson`)
```plantuml
@startjson
{
  "project": "OKF Antigravity",
  "version": "1.0.0",
  "features": [
    "Diagram-as-Code",
    "AI Agent Second Brain"
  ],
  "author": {
    "name": "よっちゃん",
    "role": "Lead Architect"
  }
}
@endjson
```

#### YAML 可視化 (`@startyaml`)
```plantuml
@startyaml
apiVersion: v1
kind: Service
metadata:
  name: my-backend-service
spec:
  selector:
    app: backend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
@endyaml
```

---

### 3.2 ネットワーク構成図 (`nwdiag`)
ネットワーク構成、サブネット、IPアドレス、接続ノードを記述します。

```plantuml
@startuml
nwdiag {
  network DMZ {
    address = "210.x.x.x/24"
    web01 [address = "210.x.x.1"];
    web02 [address = "210.x.x.2"];
  }
  network Internal {
    address = "172.16.1.0/24"
    web01;
    web02;
    db01 [address = "172.16.1.101"];
    db02 [address = "172.16.1.102"];
  }
}
@enduml
```

---

### 3.3 Salt (Wireframe GUIプロトタイピング)
画面レイアウト、ボタン、入力フォーム、テーブルなどのGUIワイヤーフレームを描画します。

```plantuml
@startsalt
{+
  <b>ユーザーログイン画面</b>
  --
  ユーザーID | "user@example.com"
  パスワード | "*******"
  [  ログイン  ] | [ キャンセル ]
  [X] ログイン状態を保持する
}
@endsalt
```

---

### 3.4 ガントチャート (Gantt Chart)
プロジェクトタスク、マイルストーン、進捗・スケジューリングを定義します。

```plantuml
@startgantt
title OKF PlantUML 構築プロジェクト
[PDF解析と構造化] lasts 2 days
[OKFモジュールドキュメント作成] lasts 3 days
[INDEX.md 更新と整合性テスト] lasts 1 days

[OKFモジュールドキュメント作成] starts at [PDF解析と構造化]'s end
[INDEX.md 更新と整合性テスト] starts at [OKFモジュールドキュメント作成]'s end
@endgantt
```

---

### 3.5 MindMap & WBS (Work Breakdown Structure)

#### MindMap (`@startmindmap`)
```plantuml
@startmindmap
* PlantUML OKF
** UML
*** シーケンス図
*** クラス図
*** アクティビティ図
** 非UML
*** ネットワーク図 (nwdiag)
*** ガントチャート
*** Wireframe (Salt)
** スタイル
*** skinparam
*** Creole
@endmindmap
```

#### WBS (`@startwbs`)
```plantuml
@startwbs
* システム開発
** 要件定義
*** ヒアリング
*** 仕様書作成
** 設計
*** 基本設計
*** 詳細設計
** 実装
*** バックエンド
*** フロントエンド
@endwbs
```

---

### 3.6 ER図 (Entity Relationship Diagram)
データベースのテーブル構造とリレーションシップを表現します。

```plantuml
@startuml
entity "users" as users {
  * id : number <<PK>>
  --
  * name : text
  * email : text
}

entity "orders" as orders {
  * id : number <<PK>>
  --
  * user_id : number <<FK>>
  * total_price : decimal
  * created_at : timestamp
}

users ||..o{ orders : "1対多"
@enduml
```

---

* [PlantUML言語リファレンス メインに戻る](file:///C:/Users/PC_User/OKF/plantuml_language_reference.md)
