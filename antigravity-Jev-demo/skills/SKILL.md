# Skill: jev-eval-runner

## 役割
生成したコードやテキスト成果物を Jev 評価スクリプトに渡し、合否判定を取得する。

## 実行コマンド
`python run_demo.py`

## 判定基準
- verdict が PASS の場合はタスク完了とする。
- FAIL の場合は指摘内容をもとに修正を再試行する。