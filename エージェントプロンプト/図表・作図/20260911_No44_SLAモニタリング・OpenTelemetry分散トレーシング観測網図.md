---
tags:
  - diagram
  - architecture
  - visual-spec
  - obsidian
  - auto-generated
summary: "OpenTelemetry Collector による Trace ID 伝搬と Jaeger / Grafana によるレイテンシ可視化構成図。"
updated: 2026-09-11
---

# 📊 No.44 SLAモニタリング・OpenTelemetry分散トレーシング観測網図 作図・設計書

## 1. 概要と目的
本ドキュメントは、最新の30テーブル構成モデルおよび状態遷移v2に基づく **No.44 SLAモニタリング・OpenTelemetry分散トレーシング観測網図** の視覚化ダイアグラム・作図仕様書です。

OpenTelemetry Collector による Trace ID 伝搬と Jaeger / Grafana によるレイテンシ可視化構成図。

---

## 2. Mermaid ダイアグラム

```mermaid
graph TD
    Client["Client Request (TraceID: 9a8b)"] --> GW["API Gateway"]
    GW --> OrderSvc["Order Service"]
    OrderSvc --> StockSvc["Stock Service"]
    
    GW -->|Span Data| OTel["OpenTelemetry Collector"]
    OrderSvc -->|Span Data| OTel
    StockSvc -->|Span Data| OTel
    
    OTel --> Jaeger["Jaeger / Grafana (分散トレース画面)"]
```

---

## 3. 作図要素・コンポーネント定義表

| 要素名 / ノード | 種別 | 主な役割・機能 | 連携対象 |
| :--- | :--- | :--- | :--- |
| **主要コンポーネント** | Engine / DB | 処理の実行および状態保持 | 連携サービス |
| **イベント / シグナル** | Message | コンテキスト間のトリガー通知 | イベントバス |

---

## 4. 運用・検証ガイド
Obsidian プレビューモードにて Mermaid ダイアグラムが正常に描画されることを確認してください。
