import csv
import json
import math
import random
import statistics
from pathlib import Path


DATA_PATH = Path(__file__).parents[1] / "raw" / "regression_sample_500.csv"
TARGET = "monthly_rent_yen"
NUMERIC_FEATURES = [
    "area_sqm",
    "station_walk_min",
    "building_age_years",
    "floor_number",
    "total_floors",
    "rooms",
    "station_daily_passengers_10k",
]
CATEGORICAL_FEATURES = ["building_structure", "ward"]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def mean(values):
    return math.fsum(values) / len(values)


def rmse(actual, predicted):
    return math.sqrt(mean([(observed - estimate) ** 2 for observed, estimate in zip(actual, predicted)]))


def mae(actual, predicted):
    return mean([abs(observed - estimate) for observed, estimate in zip(actual, predicted)])


def r_squared(actual, predicted):
    center = mean(actual)
    total = math.fsum((observed - center) ** 2 for observed in actual)
    residual = math.fsum((observed - estimate) ** 2 for observed, estimate in zip(actual, predicted))
    return 1 - residual / total if total else 0.0


def pearson(left, right):
    left_center = mean(left)
    right_center = mean(right)
    numerator = math.fsum((x - left_center) * (y - right_center) for x, y in zip(left, right))
    left_sum = math.fsum((x - left_center) ** 2 for x in left)
    right_sum = math.fsum((y - right_center) ** 2 for y in right)
    denominator = math.sqrt(left_sum * right_sum)
    return numerator / denominator if denominator else 0.0


def solve_least_squares(matrix, target):
    """Solve an overdetermined system with Householder QR decomposition."""
    values = [row[:] for row in matrix]
    outcomes = target[:]
    row_count = len(values)
    column_count = len(values[0])

    for column in range(column_count):
        norm = math.sqrt(math.fsum(values[row][column] ** 2 for row in range(column, row_count)))
        if norm < 1e-10:
            raise ValueError("Design matrix is rank-deficient.")
        alpha = -math.copysign(norm, values[column][column])
        vector = [values[column][column] - alpha]
        vector.extend(values[row][column] for row in range(column + 1, row_count))
        vector_norm = math.fsum(item * item for item in vector)
        if vector_norm < 1e-20:
            raise ValueError("Design matrix is rank-deficient.")

        for current_column in range(column, column_count):
            projection = 2 * math.fsum(
                vector[offset] * values[column + offset][current_column]
                for offset in range(len(vector))
            ) / vector_norm
            for offset, item in enumerate(vector):
                values[column + offset][current_column] -= projection * item

        projection = 2 * math.fsum(
            vector[offset] * outcomes[column + offset] for offset in range(len(vector))
        ) / vector_norm
        for offset, item in enumerate(vector):
            outcomes[column + offset] -= projection * item

    coefficients = [0.0] * column_count
    for row in range(column_count - 1, -1, -1):
        remainder = outcomes[row] - math.fsum(
            values[row][column] * coefficients[column]
            for column in range(row + 1, column_count)
        )
        coefficients[row] = remainder / values[row][row]
    return coefficients


def fit_model(training_rows, evaluation_rows, selected_features):
    numeric = [name for name in NUMERIC_FEATURES if name in selected_features]
    categorical = [name for name in CATEGORICAL_FEATURES if name in selected_features]
    centers = {name: mean([float(row[name]) for row in training_rows]) for name in numeric}
    scales = {
        name: math.sqrt(mean([(float(row[name]) - centers[name]) ** 2 for row in training_rows])) or 1.0
        for name in numeric
    }
    categories = {
        name: sorted({row[name] for row in training_rows}) for name in categorical
    }
    feature_names = ["intercept"]
    feature_names.extend(f"{name} (z)" for name in numeric)
    for name in categorical:
        feature_names.extend(f"{name}={value}" for value in categories[name][1:])

    def transform(row):
        vector = [1.0]
        vector.extend((float(row[name]) - centers[name]) / scales[name] for name in numeric)
        for name in categorical:
            vector.extend(1.0 if row[name] == value else 0.0 for value in categories[name][1:])
        return vector

    training_matrix = [transform(row) for row in training_rows]
    training_target = [float(row[TARGET]) for row in training_rows]
    coefficients = solve_least_squares(training_matrix, training_target)

    def predict(rows):
        return [math.fsum(a * b for a, b in zip(transform(row), coefficients)) for row in rows]

    training_prediction = predict(training_rows)
    evaluation_prediction = predict(evaluation_rows)
    raw_coefficients = {
        "intercept": coefficients[0] - math.fsum(
            coefficients[index + 1] * centers[name] / scales[name]
            for index, name in enumerate(numeric)
        )
    }
    standardized_effects = {}
    target_scale = statistics.pstdev(training_target) or 1.0
    for index, name in enumerate(numeric):
        coefficient = coefficients[index + 1]
        raw_coefficients[name] = coefficient / scales[name]
        standardized_effects[name] = coefficient / target_scale
    category_offset = 1 + len(numeric)
    for name in categorical:
        for index, value in enumerate(categories[name][1:]):
            coefficient = coefficients[category_offset + index]
            raw_coefficients[f"{name}={value} (vs {categories[name][0]})"] = coefficient
            standardized_effects[f"{name}={value} (vs {categories[name][0]})"] = coefficient / target_scale
        category_offset += max(0, len(categories[name]) - 1)

    return {
        "train_actual": training_target,
        "train_predicted": training_prediction,
        "test_actual": [float(row[TARGET]) for row in evaluation_rows],
        "test_predicted": evaluation_prediction,
        "train_metrics": {
            "rmse": rmse(training_target, training_prediction),
            "mae": mae(training_target, training_prediction),
            "r2": r_squared(training_target, training_prediction),
        },
        "test_metrics": {
            "rmse": rmse([float(row[TARGET]) for row in evaluation_rows], evaluation_prediction),
            "mae": mae([float(row[TARGET]) for row in evaluation_rows], evaluation_prediction),
            "r2": r_squared([float(row[TARGET]) for row in evaluation_rows], evaluation_prediction),
        },
        "coefficients_yen": raw_coefficients,
        "standardized_effects": standardized_effects,
        "test_residual_mean": mean(
            [prediction - actual for actual, prediction in zip(
                [float(row[TARGET]) for row in evaluation_rows], evaluation_prediction
            )]
        ),
    }


def round_metrics(metrics):
    return {name: round(value, 4) for name, value in metrics.items()}


def write_dashboard(rows, test_rows, model, output_path):
        actual = model["test_actual"]
        predicted = model["test_predicted"]
        residuals = [estimate - observed for observed, estimate in zip(actual, predicted)]
        rent_values = [float(row[TARGET]) for row in rows]
        wards = sorted({row["ward"] for row in rows})
        effects = sorted(
                model["standardized_effects"].items(), key=lambda item: abs(item[1]), reverse=True
        )[:10]
        payload = {
                "actual": actual,
                "predicted": predicted,
                "residuals": residuals,
                "coefficients": [{"name": name, "value": value} for name, value in effects],
                "wards": {
                        ward: [float(row[TARGET]) for row in rows if row["ward"] == ward]
                        for ward in wards
                },
                "rentRange": [min(rent_values), max(rent_values)],
        }
        data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
        metrics = model["test_metrics"]
        html = f'''<!doctype html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>東京5区の不動産賃料モデル | 合成サンプル回帰BI</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        :root {{ color-scheme: light; font-family: "Segoe UI", sans-serif; color: #172033; background: #eef2f5; }}
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; padding: 28px; }}
        header {{ max-width: 1400px; margin: 0 auto 20px; }}
        h1 {{ margin: 0 0 6px; font-size: 25px; }}
        p {{ margin: 0; color: #526174; }}
        .metrics {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; max-width: 1400px; margin: 0 auto 14px; }}
        .metric {{ padding: 14px 16px; background: #fff; border-left: 4px solid #087e8b; }}
        .metric span {{ display: block; color: #526174; font-size: 12px; }}
        .metric strong {{ display: block; margin-top: 4px; font-size: 21px; }}
        .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; max-width: 1400px; margin: auto; }}
        .chart {{ min-width: 0; height: 390px; background: #fff; border: 1px solid #d5dde5; }}
        .notice {{ max-width: 1400px; margin: 14px auto 0; font-size: 12px; }}
        @media (max-width: 760px) {{ body {{ padding: 16px; }} .grid {{ grid-template-columns: 1fr; }} .metrics {{ grid-template-columns: 1fr; }} .chart {{ height: 340px; }} }}
    </style>
</head>
<body>
    <header>
        <h1>東京5区の不動産賃料モデル | 合成サンプル回帰BI</h1>
        <p>東京5区の区名を用いた合成サンプル500件です。実際の東京の賃料相場を示すものではありません。テスト100件の予測・係数・地域差・残差を確認できます。</p>
    </header>
    <section class="metrics" aria-label="テスト指標">
        <div class="metric"><span>テスト R²</span><strong>{metrics["r2"]:.4f}</strong></div>
        <div class="metric"><span>テスト RMSE</span><strong>{metrics["rmse"]:,.0f} 円</strong></div>
        <div class="metric"><span>テスト MAE</span><strong>{metrics["mae"]:,.0f} 円</strong></div>
    </section>
    <main class="grid">
        <div class="chart" id="fit"></div>
        <div class="chart" id="effects"></div>
        <div class="chart" id="wards"></div>
        <div class="chart" id="residuals"></div>
    </main>
    <p class="notice">注意: これは既知の加算式から作った合成データの分析例です。実際の賃料相場や因果効果を示すものではありません。図はPlotly CDNの読み込みにインターネット接続が必要です。</p>
    <script>
        const data = {data_json};
        const common = {{ paper_bgcolor: "#fff", plot_bgcolor: "#fff", font: {{ color: "#172033" }}, margin: {{ l: 65, r: 22, t: 54, b: 58 }}, autosize: true }};
        const config = {{ responsive: true, displaylogo: false }};
        const low = data.rentRange[0] - 20000;
        const high = data.rentRange[1] + 20000;
        Plotly.newPlot("fit", [
            {{ x: data.actual, y: data.predicted, type: "scatter", mode: "markers", name: "テスト物件", marker: {{ color: "#087e8b", size: 8, opacity: 0.72 }} }},
            {{ x: [low, high], y: [low, high], type: "scatter", mode: "lines", name: "完全一致", line: {{ color: "#b42318", dash: "dash" }} }}
        ], {{ ...common, title: "実績賃料 vs 予測賃料", xaxis: {{ title: "実績（円）", range: [low, high] }}, yaxis: {{ title: "予測（円）", range: [low, high] }} }}, config);
        const sortedEffects = data.coefficients.slice().reverse();
        Plotly.newPlot("effects", [{{
            x: sortedEffects.map(item => item.value),
            y: sortedEffects.map(item => item.name),
            type: "bar",
            orientation: "h",
            marker: {{ color: sortedEffects.map(item => item.value >= 0 ? "#087e8b" : "#c2413b") }},
            hovertemplate: "%{{y}}<br>標準化効果: %{{x:.3f}}<extra></extra>"
        }}], {{ ...common, title: "標準化係数 | 学習データ基準", xaxis: {{ title: "標準化効果" }}, yaxis: {{ automargin: true }} }}, config);
        Plotly.newPlot("wards", Object.entries(data.wards).map(([ward, rents]) => ({{
            y: rents, type: "box", name: ward, boxpoints: "outliers", marker: {{ color: "#d28b26" }}
        }})), {{ ...common, title: "地域別の賃料分布", yaxis: {{ title: "月額賃料（円）" }}, showlegend: false }}, config);
        Plotly.newPlot("residuals", [{{
            x: data.predicted, y: data.residuals, type: "scatter", mode: "markers", name: "残差",
            marker: {{ color: "#4263a5", size: 8, opacity: 0.7 }}, hovertemplate: "予測: %{{x:,.0f}}円<br>残差: %{{y:,.0f}}円<extra></extra>"
        }}, {{
            x: [low, high], y: [0, 0], type: "scatter", mode: "lines", name: "残差0", line: {{ color: "#b42318", dash: "dash" }}
        }}], {{ ...common, title: "予測値別の残差", xaxis: {{ title: "予測賃料（円）" }}, yaxis: {{ title: "予測 - 実績（円）" }} }}, config);
    </script>
</body>
</html>
'''
        output_path.write_text(html, encoding="utf-8")


def main():
    with DATA_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    if len(rows) != 500 or len(fieldnames) != 10:
        raise ValueError(f"Expected 500 data rows and 10 columns; got {len(rows)} rows and {len(fieldnames)} columns.")
    if TARGET not in fieldnames or not set(ALL_FEATURES).issubset(fieldnames):
        raise ValueError("CSV schema does not match the expected rent-model fields.")

    missing_cells = sum(value is None or value.strip() == "" for row in rows for value in row.values())
    duplicate_rows = len(rows) - len({tuple(row[name] for name in fieldnames) for row in rows})
    rents = [float(row[TARGET]) for row in rows]

    indices = list(range(len(rows)))
    random.Random(20261001).shuffle(indices)
    split_index = int(len(rows) * 0.8)
    training_rows = [rows[index] for index in indices[:split_index]]
    test_rows = [rows[index] for index in indices[split_index:]]

    full_model = fit_model(training_rows, test_rows, ALL_FEATURES)
    area_model = fit_model(training_rows, test_rows, ["area_sqm"])
    baseline_value = mean([float(row[TARGET]) for row in training_rows])
    baseline_prediction = [baseline_value] * len(test_rows)
    baseline_actual = [float(row[TARGET]) for row in test_rows]

    ablation_groups = {
        "area": ["area_sqm"],
        "urban_access": ["station_walk_min", "station_daily_passengers_10k", "ward"],
        "building_quality": ["building_age_years", "floor_number", "total_floors", "rooms", "building_structure"],
    }
    ablations = {}
    for group, removed in ablation_groups.items():
        retained = [name for name in ALL_FEATURES if name not in removed]
        model = fit_model(training_rows, test_rows, retained)
        ablations[group] = {
            "without_group_test_metrics": round_metrics(model["test_metrics"]),
            "rmse_increase_yen_vs_full": round(model["test_metrics"]["rmse"] - full_model["test_metrics"]["rmse"], 2),
        }

    fold_indices = list(range(len(training_rows)))
    random.Random(20261002).shuffle(fold_indices)
    fold_scores = []
    for fold in range(5):
        validation_indices = [index for index in fold_indices if index % 5 == fold]
        fitting_indices = [index for index in fold_indices if index % 5 != fold]
        fold_model = fit_model(
            [training_rows[index] for index in fitting_indices],
            [training_rows[index] for index in validation_indices],
            ALL_FEATURES,
        )
        fold_scores.append(fold_model["test_metrics"]["rmse"])

    dashboard_path = (
        Path(__file__).parents[2]
        / "05_Outputs"
        / "dashboards"
        / "regression_dashboard.html"
    )
    write_dashboard(rows, test_rows, full_model, dashboard_path)

    numeric_correlations = {
        name: pearson([float(row[name]) for row in rows], rents)
        for name in NUMERIC_FEATURES
    }
    category_summary = {}
    for name in CATEGORICAL_FEATURES:
        values = {}
        for category in sorted({row[name] for row in rows}):
            category_rents = [float(row[TARGET]) for row in rows if row[name] == category]
            values[category] = {
                "count": len(category_rents),
                "mean_rent_yen": round(mean(category_rents), 2),
            }
        category_summary[name] = values

    results = {
        "data_quality": {
            "rows": len(rows),
            "columns": len(fieldnames),
            "column_names": fieldnames,
            "missing_cells": missing_cells,
            "duplicate_rows": duplicate_rows,
            "train_rows": len(training_rows),
            "test_rows": len(test_rows),
            "rent_mean_yen": round(mean(rents), 2),
            "rent_median_yen": statistics.median(rents),
            "rent_min_yen": min(rents),
            "rent_max_yen": max(rents),
        },
        "model_comparison": {
            "mean_baseline": round_metrics({
                "rmse": rmse(baseline_actual, baseline_prediction),
                "mae": mae(baseline_actual, baseline_prediction),
                "r2": r_squared(baseline_actual, baseline_prediction),
            }),
            "area_only_ols": round_metrics(area_model["test_metrics"]),
            "multiple_ols": round_metrics(full_model["test_metrics"]),
            "multiple_ols_train": round_metrics(full_model["train_metrics"]),
            "five_fold_cv_rmse_yen": {
                "folds": [round(value, 2) for value in fold_scores],
                "mean": round(mean(fold_scores), 2),
                "std": round(statistics.pstdev(fold_scores), 2),
            },
        },
        "hypothesis_tests": ablations,
        "numeric_rent_correlations": {name: round(value, 4) for name, value in numeric_correlations.items()},
        "category_mean_rent": category_summary,
        "multiple_ols_coefficients_yen": {
            name: round(value, 2) for name, value in full_model["coefficients_yen"].items()
        },
        "standardized_effects": {
            name: round(value, 4) for name, value in full_model["standardized_effects"].items()
        },
        "test_residual_mean_yen": round(full_model["test_residual_mean"], 2),
        "dashboard_path": dashboard_path.name,
        "synthetic_data_note": "The rent target is simulated from a known additive formula with random noise; results demonstrate method, not market causality.",
    }
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()