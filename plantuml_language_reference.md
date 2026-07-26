---
type: ナレッジ仕様書
title: PlantUML 言語リファレンスガイド (OKF完全版)
category: ソフトウェア開発 / 構造化ダイアグラム / AIグラフィックス
tags: [PlantUML, UML, OKF, Diagram-as-Code, KnowledgeBase]
created_at: 2026-07-27
updated_at: 2026-07-27
---

# PlantUML 言語リファレンスガイド (OKF完全版)

---

## 📋 1. 前提情報 (選択能力・メタデータ)

| 項目 | 内容 |
| :--- | :--- |
| **領域** | AIグラフィックス・仕様記述言語・ダイアグラム設計領域 |
| **タイトル** | PlantUML 言語リファレンスガイド (OKF完全版) |
| **できること** | プレーンテキスト（Diagram-as-Code）による各種UML・非UML図・ワイヤーフレーム・ガントチャート等の決定論的レンダリングとAI自律生成 |
| **実例** | システム設計書やアーキテクチャ図をコード管理し、AIエージェントによる設計図の自動生成・差分管理・セカンドブレイン検索を実現 |
| **リソース** | PlantUML Language Reference Guide (公式日本語版全586ページ) |
| **関連ドキュメント** | [PlantUML UMLダイアグラム仕様](file:///C:/Users/PC_User/OKF/plantuml_uml_diagrams.md) \| [PlantUML 非UML・データ可視化仕様](file:///C:/Users/PC_User/OKF/plantuml_non_uml_diagrams.md) \| [PlantUML スタイル・プリプロセッサ仕様](file:///C:/Users/PC_User/OKF/plantuml_styling_and_preprocessor.md) \| [OKF仕様・運用ガイド](file:///C:/Users/PC_User/OKF/okf_specification_overview.md) |
| **全体目次** | [OKFナレッジインデックス (INDEX.md)](file:///C:/Users/PC_User/OKF/INDEX.md) |

---

## 🔬 2. よっちゃん流ハイブリッド診断 (分析＆未来ベクトル)

### 🧠 Karpathy流「8つの視点」によるシステム評価

1. **Software 1.0 / 2.0 / 3.0 の共存**:
   - **1.0**: PlantUML Java / Graphviz レンダリングエンジンとテキスト構文。
   - **2.0**: ASTパース、SVG/PNG変換スクリプト、自動ビルドパイプライン。
   - **3.0**: 自然言語（意図）からLLMがPlantUMLコードを直接コンパイルし、リアルタイムで設計図を自動生成・リファクタリング。
2. **LLM as an OS**:
   - PlantUML構文が「LLMのグラフィック描画API / UIサブシステム」として機能し、テキストベースで正確な構造体を画面描画。
3. **部分的自律性 (スライダー)**:
   - 手動によるPlantUML記述から、AIエージェントによるコード解釈・シーケンス図自動起こしまでスライダー調整可能。
4. **アイアンマンスーツ (拡張)**:
   - アーキテクトやエンジニアの脳内モデルを、テキストコードとして瞬時に可視化し、チーム全体での仕様視覚化能力を拡張。
5. **Vibe Coding (意図)**:
   - 「Microservice AからBへの認証フローを描いて」という指示から、完全なシーケンス図コードをダイレクト出力。
6. **LLM Psychology (心理学)**:
   - バイナリ画像ファイルではAIが認識・編集困難な課題を、プレーンテキスト形式で保持することで「AIが迷わず推論・修正できる」確信空間を提供。
7. **Compilation Analogy (コンパイル)**:
   - `PlantUML DSL` $\rightarrow$ `Graphviz / SML` $\rightarrow$ `SVG / PNG / Vector Graphics` への多段階コンパイル構造。
8. **Build for Agents**:
   - エージェントが構文エラーなく可視化コードを出力できるよう、厳密なモジュール別構文ルールとサンプルコードを提供。

---

### 🧩 内部構造の診断 (核・質・特・欠)

- **核 (核心)**:
  - `@startuml ... @enduml` または `@startjson` / `@startsalt` 等で囲むプレーンテキストベースのダイアグラム記述プロトコル。
- **質 (品質)**:
  - バージョン管理（Git）との相性が抜群であり、差分確認（Diff）や衝突解消、CI/CDでの自動ドキュメント生成が容易。
- **特 (特性)**:
  - UML図全般から、WBS、ガントチャート、MindMap、Salt（ワイヤーフレーム）、nwdiag（ネットワーク図）まで広範な表現力を網羅。
- **欠 (欠損・課題)**:
  - 自動レイアウトエンジン（Graphviz）にレイアウト調整を依存するため、複雑な配置の細かな手動コントロールにはノウハウ（隠しリンク `-[hidden]-` や skinparam）が必要。

---

### 🚀 未来ベクトル (方・移・拡・新)

- **方 (方向性)**:
  - 設計ドキュメントの完全コード化（Diagram-as-Code）によるAIセカンドブレインとの完全統合。
- **移 (移動性)**:
  - VS Code、Obsidian、GitHub PRプレビュー、Docker、CLI、各種RAG環境へシームレスに移植・レンダリング可能。
- **拡 (拡張性)**:
  - AWS/Azure/GCP/FontAwesome等の標準ライブラリ（Standard Library）取り込みやカスタムプリプロセッサ機能による拡張。
- **新 (新規性)**:
  - 画像を保持する時代から、AIと人間がコードで対話しながら動的に設計図を生み出すインタラクティブな開発モデルの確立。

---

## 💬 3. 対話スクリプト & タイムライン (ずんだもん・めたん解説)

### ⏱️ タイムライン
| タイムスタンプ | セクション名 | 主な内容 |
| :--- | :--- | :--- |
| **00:00** | イントロダクション：設計図の画像管理の限界 | 画像ファイルをパワポやVisioで管理するとAIが読めず、更新が止まる問題。 |
| **02:15** | PlantUML と Diagram-as-Code の革命 | テキストで図を描くことで、Git管理とAI自動編集が可能になる仕組み。 |
| **05:30** | OKFによるPlantUMLナレッジのモジュール化 | UML図、非UML・可視化、スタイル・プリプロセッサの3大モジュール構成。 |
| **09:00** | UML基本ダイアグラム（シーケンス・クラス・アクティビティ） | システム設計の中核をなす各記法のポイントとAI出力時のコツ。 |
| **12:45** | 非UMLダイアグラム（ネットワーク・ガント・MindMap・Salt） | 業務フローやインフラ構成、GUIプロトタイプまでテキスト化する技法。 |
| **16:20** | skinparam と Creole 装飾 | リッチな美しさ・ダークモード対応とテキスト装飾の極意。 |
| **19:00** | まとめと活用ガイド | AIエージェントと対話しながら設計図をリアルタイム更新するセカンドブレイン運用。 |

---

### 🗣️ 対話文字起こしログ

> **[00:00]**  
> **ずんだもん**: 「みんな、仕様書のシステム構成図やシーケンス図をパワポや画像で管理していて、修正が面倒でドキュメントが古くなっちゃった経験はないのだ？AIに画像を見せても細部が読み取れなかったりするのだ！」  
> **めたん**: 「そうね。設計図をバイナリ画像で保持していると、バージョン管理も難しいし、AIエージェントが自律的に修正・更新することもできないわ。それを解決するのが『PlantUML』による Diagram-as-Code なのよ。」  
>
> **[02:15]**  
> **ずんだもん**: 「PlantUMLは、シンプルなテキストを書くだけで、きれいで正確な図を自動生成してくれる魔法の言語なのだ！今回、公式日本語ガイド586ページ分をぜんぶOKF構造に整えたのだ！」  
> **めたん**: 「OKF（Open Knowledge Format）として整理したことで、人間にとってもAIにとっても必要な構文やサンプルコードを即座に探索・ロードできるようになったわ。今回は3つのモジュールに分けて網羅しているのよ。」  

---

## 📚 4. PlantUML OKF モジュールマップ

PlantUML の膨大な言語仕様を、目的別・機能別に以下の3つのOKFモジュールに分割・接続しています。

| モジュール名 | 収録内容・対応図種 | 参照リンク |
| :--- | :--- | :--- |
| **UMLダイアグラム仕様** | シーケンス図、ユースケース図、クラス図、オブジェクト図、アクティビティ図（新旧）、コンポーネント図、デプロイ図、ステート図、タイミング図 | 📄 [plantuml_uml_diagrams.md](file:///C:/Users/PC_User/OKF/plantuml_uml_diagrams.md) |
| **非UML・データ可視化仕様** | JSON構造図、YAML構造図、ネットワーク図 (nwdiag)、Salt (GUI Wireframe)、ArchiMate、ガントチャート、MindMap、WBS、ER図 | 📄 [plantuml_non_uml_diagrams.md](file:///C:/Users/PC_User/OKF/plantuml_non_uml_diagrams.md) |
| **スタイル・プリプロセッサ仕様** | Creole テキスト装飾、スプライト定義、skinparam スタイル設定、プリプロセッサ (`!include`, `!define`, `!procedure`)、Unicode、標準ライブラリ (AWS/Azure/FontAwesome) | 📄 [plantuml_styling_and_preprocessor.md](file:///C:/Users/PC_User/OKF/plantuml_styling_and_preprocessor.md) |

---

## 🛠️ 5. 運用・検証ガイドライン (検証コード・実行方法)

PlantUMLコードの正常性や描画テストを行うための標準検証手順です。

### 1. ローカルCLIでのレンダリング検証
```bash
# PlantUML JAR を使用した PNG 生成
java -jar plantuml.jar example.puml

# SVG 形式での高速出力
java -jar plantuml.jar -tsvg example.puml
```

### 2. Python (plantuml) スクリプトでの動的検証
```python
from plantuml import PlantUML

# PlantUML サーバーへのレンダリングテスト
server = PlantUML(url='http://www.plantuml.net/plantuml/img/')
png_bytes = server.processes("""
@startuml
Alice -> Bob: OKF PlantUML Verification
Bob --> Alice: Clean & Valid
@enduml
""")

with open("verification_output.png", "wb") as f:
    f.write(png_bytes)
print("PlantUML Rendering Verification Passed!")
```

### 3. AIエージェント運用ルールの確認
* 記述時は必ず `@startuml` と `@enduml`（または対象図種の開始・終了タグ）で囲むこと。
* 複雑なレイアウト問題が発生した場合は、`-[hidden]-` リンクで配置をアシストすること。
* セカンドブレイン連携時は、各詳細モジュール (`plantuml_uml_diagrams.md` 等) から構文パターンを参照すること。

---

* [OKFナレッジインデックスに戻る](file:///C:/Users/PC_User/OKF/INDEX.md)
