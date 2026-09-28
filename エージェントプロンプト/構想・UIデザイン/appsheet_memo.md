# AppSheet 注文管理アプリ開発メモ

## 現在の課題
注文ステータスが「出荷完了」に変更されたら、顧客に自動でメール通知を送るBotを作成したい。
しかし、メールの宛先（顧客のメールアドレス）が注文テーブルにはなく、紐づく「顧客テーブル」にしか保存されていない。

## テーブル構造
1. **Customers (顧客)**:
   * CustomerID (Key)
   * Name
   * Email
2. **Orders (注文)**:
   * OrderID (Key)
   * CustomerID (Ref -> Customers)
   * OrderDate
   * Status (Enum: "受付中", "準備中", "出荷完了")

## 実現したいこと
AppSheetのBot設定において、どのようにして親テーブル（Customers）のEmailを取得し、自動メール送信のアクションをトリガーすれば良いか？
