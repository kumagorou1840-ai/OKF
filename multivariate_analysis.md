# Antigravity OS ナレッジドキュメント: 多変量解析自動実行

---

## 📋 1. 前提情報 (選択能力・メタデータ)

| 項目 | 内容 |
| :--- | :--- |
| **領域** | データサイエンス・数理モデリング領域 |
| **タイトル** | 多変量解析自動実行（重回帰分析） |
| **できること** | どの要因が最も結果（目的変数）に影響しているかを統計的に検証・特定 |
| **実例** | 成約率に対して「駅距離」「築年数」「価格」の相関・影響度を計測 |
| **リソース** | [Google Colab Notebook](https://colab.research.google.com/drive/1RPiA7dhpoKtqAt1WzNJCIEA8z2BopldK#scrollTo=BInDSV1DkskD) |
| **関連ドキュメント** | [OKF実践活用ガイド](file:///C:/Users/PC_User/OKF/okf_practical_usage.md) \| [Git完全ハンドリング](file:///C:/Users/PC_User/OKF/git_unpushed_sync.md) \| [OKF仕様・運用ガイド](file:///C:/Users/PC_User/OKF/okf_specification_overview.md) \| [OKF AIブレイン構築ガイド](file:///C:/Users/PC_User/OKF/okf_brain_build_guide.md) |
| **全体目次** | [OKFナレッジインデックス (INDEX.md)](file:///C:/Users/PC_User/OKF/INDEX.md) |

---

## 🔬 2. よっちゃん流ハイブリッド診断 (分析＆未来ベクトル)

### 🧩 内部構造の診断 (核・質・特・欠)

- **核 (核心)**:
  - 複数要因（説明変数）が年間売上（目的変数）に与える影響度を重回帰分析（OLS: 最小二乗法）および標準化回帰係数を用いて定量的に比較評価する。
- **質 (品質)**:
  - `statsmodels` を用いた統計学的厳密性（P値 $\le 0.05$ の有意性確認）と、単位の異なる変数を公平に評価する標準化処理が組み込まれている。
- **特 (特性)**:
  - 1000件の合成データを生成し、要因比較（標準化係数の絶対値評価）と結果の可視化（散布図・影響度棒グラフ）までを一気通貫で実行可能。
- **欠 (欠損・課題)**:
  - 現状の基本モデルでは説明変数間の相関（多重共線性: VIF）の検証が未実施。
  - 線形関係を前提としており、非線形な影響や変数間の交互作用（例: 経験年数×資料の質）は未考慮。

### 🚀 未来ベクトル (方・移・拡・新)

- **方 (方向性)**:
  - データ駆動型による営業施策の優先順位決定（例: 研修時間の増加より「資料の質向上」へリソース集中）。
- **移 (移動性)**:
  - 不動産の成約要因分析、WEB広告のCVR要因分析、カスタマーサクセスの解約率分析など異分野へ即座に応用可能。
- **拡 (拡張性)**:
  - VIF（分散拡大係数）計算による多重共線性チェック、Lasso/Ridge回帰や決定木系モデルへの分析手法拡張。
- **新 (新規性)**:
  - 分析結果をLLMエージェントが自動解釈し、経営・現場向けの「具体的な改善アクションプラン」を自動生成するシステムへの昇華。

---

## 💬 3. 対話プロンプト & コンテキスト

### 👤 ユーザープロンプト
> 当社の営業担当者の年間売上ダミーデータが1000件あります。dataを作成し、これに対して、研修受講時間、顧客訪問数、提案資料の質（スコア）、営業経験年数が売上成績にどれだけ影響しているかを多変量解析で統計的に検証し、最も影響の大きい要因を特定してください。

### 🤖 Antigravity OS 回答要約
複数の説明変数（研修受講時間、顧客訪問数、提案資料の質、営業経験年数）が目的変数（年間売上）に与える影響度を、**重回帰分析（OLS）** と **標準化回帰係数** を用いて分析・特定する手順とPythonスクリプトを提供します。

---

## 💻 4. 実装コード (Python / Colab対応)

```python
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================================
# 1. データの準備（ダミーデータ 1,000件の生成）
# ==========================================
np.random.seed(42) # 再現性の確保
num_sales_reps = 1000

# 説明変数
training_hours = np.random.normal(loc=50, scale=15, size=num_sales_reps)
training_hours[training_hours < 0] = 0

customer_visits = np.random.normal(loc=100, scale=30, size=num_sales_reps)
customer_visits[customer_visits < 0] = 0

proposal_quality = np.random.normal(loc=75, scale=10, size=num_sales_reps)
proposal_quality = np.clip(proposal_quality, 1, 100)

years_experience = np.random.normal(loc=5, scale=2, size=num_sales_reps)
years_experience[years_experience < 0] = 0

# 目的変数 (年間売上 - 万円)
sales = (
    500 + 
    training_hours * 5 +       
    customer_visits * 10 +    
    proposal_quality * 20 +   
    years_experience * 30 +   
    np.random.normal(loc=0, scale=500, size=num_sales_reps)
)
sales[sales < 0] = 0

# DataFrame構築
data = pd.DataFrame({
    '年間売上': sales,
    '研修受講時間': training_hours,
    '顧客訪問数': customer_visits,
    '提案資料の質': proposal_quality,
    '営業経験年数': years_experience
})

print("■ データ確認 (先頭5件):")
print(data.head())

# ==========================================
# 2. 重回帰分析の実行
# ==========================================
y = data['年間売上']
X_vars = ['研修受講時間', '顧客訪問数', '提案資料の質', '営業経験年数']
X = data[X_vars]
X_with_const = sm.add_constant(X)

# OLSモデルの構築と学習
model = sm.OLS(y, X_with_const)
results = model.fit()

# ==========================================
# 3. 標準化係数の算出と最影響要因の特定
# ==========================================
def get_standardized_coefs(ols_results, X_df, y_series):
    b = ols_results.params.drop('const')
    sx = X_df.std()
    sy = y_series.std()
    return b * (sx / sy)

std_coefs = get_standardized_coefs(results, X, y)

print("\n" + "="*50)
print("■ 分析結果サマリー")
print("="*50)
print(results.summary())

print("\n■ 標準化回帰係数 (影響度の比較):")
print(std_coefs.sort_values(ascending=False))

most_influential = std_coefs.abs().idxmax()
print(f"\n★ 最も年間売上に影響が大きい要因: 【 {most_influential} 】 (標準化係数: {std_coefs[most_influential]:.4f})")

# ==========================================
# 4. 可視化
# ==========================================
# (1) 各要因と売上の散布図＋回帰直線
sns.pairplot(data, y_vars=['年間売上'], x_vars=X_vars, kind='reg', height=3.5)
plt.suptitle('各要因と年間売上の関係性', y=1.03)
plt.show()

# (2) 標準化係数の絶対値比較グラフ
plt.figure(figsize=(8, 5))
std_coefs.abs().sort_values(ascending=False).plot(kind='bar', color='skyblue', edgecolor='navy')
plt.title('年間売上に対する影響度 (標準化回帰係数の絶対値)')
plt.ylabel('標準化回帰係数 (絶対値)')
plt.xticks(rotation=0)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()
```

---

## 📊 5. 結果解釈ガイドライン

1. **決定係数 ($R^2$)**:
   - モデル全体の説明力を示します（1に近いほどデータによく適合）。
2. **P値 ($P > |t|$)**:
   - 有意水準 $0.05$ 未満であれば、その要因が売上に与える影響は「統計的に有意」と判断できます。
3. **標準化回帰係数 (Standardized Coefficient)**:
   - 単位（時間、回数、スコア、年数）の違いを揃えて比較するための指標。絶対値が大きいほど、結果（年間売上）に対するインパクトが大きいです。
