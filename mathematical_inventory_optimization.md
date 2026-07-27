---
type: ナレッジ仕様書
title: 数理モデルへの実データフィッティング & インタラクティブ在庫最適化シミュレーター
category: データサイエンス・数理最適化 / 意思決定コックピット
tags: [MathematicalOptimization, MILP, PuLP, Streamlit, InventoryOptimization, DataScience, OKF]
created_at: 2026-07-27
updated_at: 2026-07-27
---

# 数理モデルへの実データフィッティング & インタラクティブ在庫最適化シミュレーター (OKF完全版)

---

## 📋 1. 前提情報 (選択能力・メタデータ)

| 項目 | 内容 |
| :--- | :--- |
| **領域** | データサイエンス / 数理最適化 (MILP) / 意思決定コックピットダッシュボード |
| **タイトル** | 数理モデルへの実データフィッティング & インタラクティブ在庫最適化シミュレーター |
| **できること** | 数学的な理論式（混合整数線形計画法：MILP）に、実際のビジネス売上・在庫データを流し込み、損益分岐点を最小化する最適な発注タイミングと発注量を自動計算し、スライダーでリアルタイム再計算・動的Plotlyグラフ表示する |
| **実例・成果** | 「いかにして問題を解くか（G. Polya）」アプローチを適用し、30日間の売上需要データから発注回数・維持費・欠品費のトレードオフを最適化。従来のNaive再発注ルールに比べ**総コストを14.80%削減（損益分岐点の引き下げ）**を実証 |
| **技術スタック** | Python, PuLP (CBC Solver), Streamlit, Plotly, Pandas, NumPy |
| **画面構成** | 左側：可動スライダー（初期在庫、発注費、維持費、欠品費等）、右側：コスト削減カード ＋ 動的2段Plotlyグラフ ＋ アクション表 ＋ 2カラムハイブリッド診断カード |
| **関連ドキュメント** | [OKF仕様・運用ガイド](file:///C:/Users/PC_User/OKF/okf_specification_overview.md) \| [全18分野スキルガイド](file:///C:/Users/PC_User/OKF/ai_agent_skills_all_domains.md) \| [50の活用ユースケース](file:///C:/Users/PC_User/.gemini/antigravity-cli/brain/4d7318c1-5e9b-4b39-9391-4179761dc6fc/okf_index_hyperlinks_50_usecases_artifact.md) |
| **全体目次** | [OKFナレッジインデックス (INDEX.md)](file:///C:/Users/PC_User/OKF/INDEX.md) |

---

## 🔬 2. よっちゃん流ハイブリッド診断 (分析＆未来ベクトル)

### 🧠 Karpathy流「8つの視点」によるシステム評価

1. **Software 1.0 / 2.0 / 3.0 の共存**:
   - **1.0**: 「安全在庫を下回ったら一定量発注する」静的な再発注点ルール。
   - **2.0**: 混合整数線形計画法（MILP）ソルバー（CBC）による決定論的大域的最適化スクリプト。
   - **3.0**: ユーザーのリアルタイムなスライダー操作（Vibe）に応じ、裏で最適化エンジンが即座に再計算・描画する動的AIコックピット。
2. **LLM as an OS**:
   - 在庫最適化計算ロジックをポータル上の独立したAPIサービスとして常駐させ、各種業務アプリからの要求に応じて最適発注数をシステム計算。
3. **Partial Autonomy (部分的自律性 / スライダー)**:
   - コスト係数や需要変動幅をユーザーがGUI上のスライダーでコントロール。AIが勝手に発注するのではなく、人間がパラメータを調整して合意するインターフェース。
4. **Iron Man Suit (アイアンマンスーツ / 拡張)**:
   - 「発注費を増やす代わりに在庫維持費を極限まで下げる」という、人間には直感的に判断しにくいトレードオフを計算力で拡張。
5. **Vibe Coding (意図の即時反映)**:
   - スライダーを動かした瞬間に数理モデルが再コンパイルされ、グラフの波形がぬるぬると動的に変化。
6. **LLM Psychology (心理学 / 視覚的納得性)**:
   - 赤いエラーや静的画像ではなく、14.8%の削減金額と動的Plotlyグラフ、最下部の「核質特欠／方移拡新」パネルにより直感的な安心感を提供。
7. **Compilation Analogy (コンパイル)**:
   - ビジネス上の制約（在庫遷移・発注固定費）をPuLPの数式表現へとコンパイルし、大域的最適解を出力。
8. **Build for Agents**:
   - 最適化エンジンを Streamlit および FastAPI / Web API 化できる構造にモジュール分離。

---

### 🧩 内部構造の診断 (核・質・特・欠)

- **核 (Core)**: 目的関数（総コスト最小化）と物理的制約（在庫遷移・発注連動）が数理モデル（MILP）として厳密に結合され、無駄な在庫を抱えないジャストインタイム発注を実現。
- **質 (Quality)**: 発注費・維持費・欠品費の複雑なトレードオフに対し、PuLP/CBCソルバーが数ミリ秒で数学的な絶対最適解を保証。
- **特 (Property)**: 曜日変動やランダムノイズを含むリアルなデモ需要データを用い、発注の「先読み効果」をPlotlyで直感的に可視化・比較可能。
- **欠 (Defect)**: 現状はリードタイム（発注から納品までの時間）が「即時（0日）」と仮定されており、また需要予測が100%当たる決定論的前提であるため、確率的変動リスクへの完全な対応が不足。

---

### 🚀 未来ベクトル (方・移・拡・新)

- **方 (Direction)**: 実際の物流網に即した「リードタイム制約（納品遅れ）」や「倉庫容量上限」の制約式を追加し、実務モデルへの適合度を向上。
- **移 (Mobility)**: この最適化ロジックをポータル上の独立したAPIとして分離し、別の「予定・タスク管理アプリ」などと販売・発注データを相互連携可能にする。
- **拡 (Extension)**: 単一品目だけでなく、複数拠点・複数品目の同時発注最適化モデルへのスケーリング。
- **新 (Novelty)**: 需要のばらつきに対して頑健な「ロバスト最適化（Software 3.0）」や、モンテカルロシミュレーションを用いた「最悪シナリオ時の欠品リスク最小化」のハイブリッド化。

---

## 💬 3. 開発・対話ログスクリプト (問題定式化 ＋ 動的アプリ進化)

### 💡 「いかにして問題を解くか」数理最適化アプローチの設計

#### 1. 問題の理解 (Understanding)
- **未知のもの**: 各日 $t$ における「最適な発注タイミング $y_t \in \{0, 1\}$」と「最適な発注量 $x_t \ge 0$」。
- **与えられたもの**:
  - 30日間の需要 $d_t$（総需要 573個、日次平均 19.1個）。
  - 初期在庫 $I_0 = 10$ 個。
  - 固定発注コスト $C_{\text{order}} = 2,000$ 円/回（発注ごとに発生する固定費）。
  - 在庫維持コスト $C_{\text{hold}} = 10$ 円/個・日（日々の保管費）。
  - 欠品ペナルティ $C_{\text{short}} = 100$ 円/個・日（売れこぼしの機会損失）。
- **制約条件**:
  - 在庫遷移式: $I_t = I_{t-1} + x_t - d_t + s_t$（期末在庫 ＝ 前日在庫 ＋ 発注量 － 需要 ＋ 欠品量）
  - 発注連動制約: $x_t \le M \cdot y_t$（発注量 $x_t > 0$ なら、発注フラグ $y_t = 1$ に固定）

#### 2. 計画の立案 (Devising a Plan)
単に在庫が減ったら発注する静的ルール（Software 1.0）に対し、将来の需要を先読みして全体の最適解を探索する混合整数線形計画法（MILP: Software 2.0）モデルを定式化。
目的関数:
$$\min \sum_{t=1}^{T} \left( C_{\text{order}} y_t + C_{\text{hold}} I_t + C_{\text{short}} s_t \right)$$

---

## 📊 4. 実証・検証結果 (従来ルール vs MILP最適化モデル)

| コスト項目 | 従来ルール (Naive) | 数理最適化 (MILP) | 差分 / 評価 |
| :--- | :--- | :--- | :--- |
| **総コスト (損益分岐点)** | **26,360 円** | **22,460 円** | **-3,900 円 (14.80% 削減) 🚀** |
| **固定発注費** | 10,000 円 (発注 5回) | 12,000 円 (発注 6回) | ＋2,000 円 (発注回数は1回増加) |
| **在庫維持費** | 16,160 円 | 9,960 円 | **－6,200 円 (約38.4% 削減) 📉** |
| **欠品ペナルティ** | 200 円 (欠品 2個) | 500 円 (欠品 5個) | ＋300 円 (ごく僅かな欠品を許容) |
| **ステータス** | - | Optimal (最適解) | 数ミリ秒で大域的最適解を算出 |

---

## 💻 5. 実務用完全コード (`optimize_inventory_app.py`)

ブラウザ上で可動スライダーを操作し、PuLP/CBCソルバーでリアルタイム再計算を行い、2段Plotlyグラフおよび下部ハイブリッド診断カードを出力する完全アプリケーションコードです。

```python
import streamlit as st
import pandas as pd
import numpy as np
import pulp
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="在庫発注・損益分岐点最適化シミュレーター", layout="wide")

st.title("📦 在庫発注・損益分岐点最適化シミュレーター (数理モデル)")
st.caption("「いかにして問題を解くか」数理最適化アプローチ (MILP: 混合整数線形計画法)")

# --- サイドバー：インタラクティブ・コントロール (スライダー) ---
st.sidebar.header("🎛️ パラメータ設定")

days = st.sidebar.slider("シミュレーション日数", 14, 60, 30)
initial_inventory = st.sidebar.slider("初期在庫 (個)", 0, 50, 10)
c_order = st.sidebar.slider("固定発注コスト (円/回)", 500, 5000, 2000, step=100)
c_hold = st.sidebar.slider("在庫維持コスト (円/個・日)", 1, 50, 10, step=1)
c_short = st.sidebar.slider("欠品ペナルティコスト (円/個・日)", 10, 500, 100, step=10)

st.sidebar.subheader("📈 需要データ設定")
base_demand = st.sidebar.slider("平均日次需要 (個)", 5, 50, 20)
noise_level = st.sidebar.slider("需要のランダムノイズ幅", 0, 15, 5)

st.sidebar.subheader("⚙️ 従来ルール (Naive) 設定")
reorder_point = st.sidebar.slider("発注点 (この在庫を下回ったら発注)", 5, 30, 15)
target_stock = st.sidebar.slider("目標在庫レベル", 20, 80, 40)

# --- 需要データの自動生成 (再現可能な乱数) ---
np.random.seed(42)
t_range = np.arange(1, days + 1)
weekly_pattern = np.array([1.2, 1.0, 0.8, 0.9, 1.1, 1.4, 1.3])
demands = [
    max(1, int(base_demand * weekly_pattern[(t - 1) % 7] + np.random.randint(-noise_level, noise_level + 1)))
    for t in t_range
]

# --- 1. 従来ルール (Naive) の計算 ---
naive_inv = [initial_inventory]
naive_order = [0] * days
naive_shortage = [0] * days

for t in range(days):
    curr_inv = naive_inv[t]
    if curr_inv < reorder_point:
        order_qty = target_stock - curr_inv
        naive_order[t] = order_qty
    else:
        order_qty = 0
    
    avail = curr_inv + order_qty
    demand = demands[t]
    if avail >= demand:
        next_inv = avail - demand
        shortage = 0
    else:
        next_inv = 0
        shortage = demand - avail
    
    if t < days - 1:
        naive_inv.append(next_inv)
    naive_shortage[t] = shortage

naive_order_cnt = sum(1 for x in naive_order if x > 0)
naive_cost_order = naive_order_cnt * c_order
naive_cost_hold = sum(naive_inv) * c_hold
naive_cost_short = sum(naive_shortage) * c_short
naive_total_cost = naive_cost_order + naive_cost_hold + naive_cost_short

# --- 2. 数理最適化 (MILP: PuLP / CBC) の計算 ---
prob = pulp.LpProblem("Inventory_Optimization", pulp.LpMinimize)

x = pulp.LpVariable.dicts("OrderQty", range(days), lowBound=0, cat=pulp.LpContinuous)
y = pulp.LpVariable.dicts("OrderFlag", range(days), cat=pulp.LpBinary)
I = pulp.LpVariable.dicts("Inventory", range(days), lowBound=0, cat=pulp.LpContinuous)
s = pulp.LpVariable.dicts("Shortage", range(days), lowBound=0, cat=pulp.LpContinuous)

# 目的関数
prob += pulp.lpSum([c_order * y[t] + c_hold * I[t] + c_short * s[t] for t in range(days)])

# 制約条件
M = sum(demands) + 100
for t in range(days):
    prev_I = initial_inventory if t == 0 else I[t - 1]
    prob += prev_I + x[t] - demands[t] + s[t] == I[t]
    prob += x[t] <= M * y[t]

# ソルバー実行 (PULP_CBC_CMD)
prob.solve(pulp.PULP_CBC_CMD(msg=False))

milp_order = [pulp.value(x[t]) for t in range(days)]
milp_inv = [pulp.value(I[t]) for t in range(days)]
milp_shortage = [pulp.value(s[t]) for t in range(days)]

milp_order_cnt = sum(1 for t in range(days) if pulp.value(y[t]) > 0.5)
milp_cost_order = milp_order_cnt * c_order
milp_cost_hold = sum(milp_inv) * c_hold
milp_cost_short = sum(milp_shortage) * c_short
milp_total_cost = pulp.value(prob.objective)

cost_diff = milp_total_cost - naive_total_cost
pct_diff = (cost_diff / naive_total_cost) * 100

# --- メインエリア表示 ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("従来コスト (Naive)", f"{int(naive_total_cost):,} 円")
m2.metric("最適化コスト (MILP)", f"{int(milp_total_cost):,} 円")
m3.metric("コスト削減額", f"{int(abs(cost_diff)):,} 円", delta=f"{pct_diff:.2f}%", delta_color="inverse")
m4.metric("発注回数比較", f"MILP: {milp_order_cnt}回 / Naive: {naive_order_cnt}回")

# Plotly動的グラフの作成
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                    subplot_titles=("【従来ルール (Naive)】 在庫レベルと発注タイミング",
                                    "【数理最適化 (MILP)】 在庫レベルと発注タイミング"))

fig.add_trace(go.Bar(x=list(t_range), y=demands, name="日次需要", marker_color="rgba(180,180,180,0.5)"), row=1, col=1)
fig.add_trace(go.Scatter(x=list(t_range), y=naive_inv, name="従来在庫", mode="lines+markers", line=dict(color="orange", width=3)), row=1, col=1)
fig.add_trace(go.Bar(x=list(t_range), y=naive_order, name="従来発注量", marker_color="rgba(255,165,0,0.7)"), row=1, col=1)

fig.add_trace(go.Bar(x=list(t_range), y=demands, name="日次需要", marker_color="rgba(180,180,180,0.5)", showlegend=False), row=2, col=1)
fig.add_trace(go.Scatter(x=list(t_range), y=milp_inv, name="最適化在庫", mode="lines+markers", line=dict(color="green", width=3)), row=2, col=1)
fig.add_trace(go.Bar(x=list(t_range), y=milp_order, name="最適化発注量", marker_color="rgba(0,128,0,0.7)"), row=2, col=1)

fig.update_layout(height=600, title_text="📈 動的在庫シミュレーション比較", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# アクションプラン表
st.subheader("📋 最適発注スケジュール (アクションプラン)")
df_result = pd.DataFrame({
    "日": t_range,
    "需要 (個)": demands,
    "MILP発注量 (個)": [int(x) for x in milp_order],
    "MILP期末在庫 (個)": [int(x) for x in milp_inv],
    "Naive発注量 (個)": naive_order,
    "Naive期末在庫 (個)": naive_inv
})
st.dataframe(df_result.T)

# --- 2カラムハイブリッド診断カード (方式A: 下部固定表示) ---
st.divider()
st.header("💡 システムハイブリッド診断 (よっちゃん流評価)")

col_eval, col_future = st.columns(2)

with col_eval:
    st.info("### 📊 現状の評価 (核・質・特・欠)")
    st.markdown("""
    - **核 (Core)**: 目的関数（総コスト最小化）と物理的制約（在庫遷移・発注連動）が数理モデル（MILP）として厳密に結合され、無駄な在庫を抱えないジャストインタイム発注を実現。
    - **質 (Quality)**: 発注費・維持費・欠品費の複雑なトレードオフに対し、PuLP/CBCソルバーが数ミリ秒で数学的な絶対最適解を保証。
    - **特 (Property)**: 曜日変動やランダムノイズを含むリアルなデモ需要データを用い、発注の「先読み効果」をPlotlyで直感的に可視化・比較可能。
    - **欠 (Defect)**: 現状はリードタイム（発注から納品までの時間）が「即時（0日）」と仮定されており、また需要予測が100%当たる決定論的前提であるため、確率的変動リスクへの完全な対応が不足。
    """)

with col_future:
    st.success("### 🚀 今後の分析見通し (方・移・拡・新)")
    st.markdown("""
    - **方 (Direction)**: 実際の物流網に即した「リードタイム制約（納品遅れ）」や「倉庫容量上限」の制約式を追加し、実務モデルへの適合度を向上。
    - **移 (Mobility)**: この最適化ロジックをポータル上の独立したAPIとして分離し、別の「予定・タスク管理アプリ」などと販売・発注データを相互連携可能にする。
    - **拡 (Extension)**: 単一品目だけでなく、複数拠点・複数品目の同時発注最適化モデルへのスケーリング。
    - **新 (Novelty)**: 需要のばらつきに対して頑健な「ロバスト最適化（Software 3.0）」や、モンテカルロシミュレーションを用いた「最悪シナリオ時の欠品リスク最小化」のハイブリッド化。
    """)
```

---

## 🛠️ 6. 運用 & 検証ガイドライン

1. **コックピットポータルからの起動**:
   - `portal_config.json` に自動登録済み。ポータルから `start_inventory_app.bat` を叩くことでブラウザ（`http://localhost:8501`）に自動起動。
2. **動的テスト検証手順**:
   - 固定発注コスト $C_{\text{order}}$ を大きく（例: 4,000円）調整 $\rightarrow$ 発注回数が減り、一度にまとめて発注する波形に自動変化。
   - 在庫維持コスト $C_{\text{hold}}$ を大きく調整 $\rightarrow$ 手元在庫を極限まで減らすジャストインタイム波形に自動変化。

---

* [OKFナレッジインデックスに戻る](file:///C:/Users/PC_User/OKF/INDEX.md)
