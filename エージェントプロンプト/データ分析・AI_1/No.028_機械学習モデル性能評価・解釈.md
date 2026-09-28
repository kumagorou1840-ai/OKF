---
id: No.028
title: 機械学習モデル性能評価・解釈
category: データ分析・AI
skills:
  - ml-plotly-dash-helper
version: 1.0.0
---

# タスク指示: 機械学習モデル性能評価・解釈

## 目的
構築済み機械学習モデルの汎化性能を検証し、SHAP値等を用いて予測根拠をブラックボックスから可視化する。

## 実行ステップ
1. **検証指標集計**: ROC-AUC、F1スコア、RMSE、MAE等の集計。
2. **モデル解釈（XAI）**: TreeSHAP / Permutation Importanceによる特徴量寄与度算出。
3. **Plotly可視化**: ROC曲線、リフトチャート、SHAP Summary Plotの描画。
4. **局所的説明**: 特定サンプルに対する推論根拠のブレイクダウン。
5. **モデル健全性レポート**: リーケージチェックと運用モニタリング指針の提示。
