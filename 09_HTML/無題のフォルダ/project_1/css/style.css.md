@charset "UTF-8";

/* ===================================================
   1. カラー変数の一元定義
   =================================================== */
:root {
  --color-primary: #4338ca;      /* メイン（インディゴ） */
  --color-primary-bg: #e0e7ff;
  --color-sky: #0284c7;          /* リンク・画像セクション */
  --color-emerald: #059669;      /* ToDoリスト */
  --color-amber: #d97706;        /* テーブル */
  --color-purple: #7c3aed;       /* フォーム */
  --color-purple-light: #faf5ff;
  --color-text-main: #334155;    /* 本文文字色 */
  --color-bg-base: #f8fafc;      /* ページ背景色 */
}

/* ===================================================
   2. 全体基本設定
   =================================================== */
body {
  font-family: sans-serif;
  line-height: 1.6;
  color: var(--color-text-main);
  background: linear-gradient(135deg, var(--color-bg-base), #f1f5f9);
  max-width: 680px;
  margin: 40px auto;
  padding: 0 20px;
}

/* ===================================================
   3. 見出し
   =================================================== */
h1 {
  color: var(--color-primary);
  background-color: var(--color-primary-bg);
  border-left: 6px solid var(--color-primary);
  padding: 10px 14px;
  border-radius: 4px;
}

h2 {
  margin-top: 36px;
  padding-bottom: 6px;
  font-size: 1.25rem;
}

h2.section-link  { color: var(--color-sky);     border-bottom: 2px solid #38bdf8; }
h2.section-todo  { color: var(--color-emerald); border-bottom: 2px solid #34d399; }
h2.section-table { color: var(--color-amber);   border-bottom: 2px solid #fbbf24; }
h2.section-form  { color: var(--color-purple);  border-bottom: 2px solid #a78bfa; }

/* ===================================================
   4. リンクと画像
   =================================================== */
a {
  color: var(--color-sky);
  text-decoration: none;
  font-weight: bold;
}

a:hover {
  text-decoration: underline;
}

img {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
}

/* ===================================================
   5. リスト
   =================================================== */
ul {
  background-color: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  padding: 16px 36px;
  color: #065f46;
}

/* ===================================================
   6. テーブル
   =================================================== */
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
  border-radius: 6px;
  overflow: hidden;
}

th, td {
  border: 1px solid #fed7aa;
  padding: 10px 12px;
  text-align: left;
}

th {
  background-color: #ffedd5;
  color: #9a3412;
  font-weight: 600;
}

td {
  background-color: #fffaf0;
}

/* ===================================================
   7. フォーム要素
   =================================================== */
form {
  background-color: var(--color-purple-light);
  border: 1px solid #e9d5ff;
  border-radius: 8px;
  padding: 24px;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: inline-block;
  margin-bottom: 4px;
  font-weight: 600;
  color: #5b21b6;
}

input[type="text"],
select {
  width: 100%;
  padding: 8px;
  border: 1px solid #c084fc;
  border-radius: 4px;
  box-sizing: border-box;
  background-color: #ffffff;
}

button[type="submit"] {
  background: linear-gradient(90deg, #7c3aed, #ec4899);
  color: #ffffff;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: opacity 0.2s;
}

button[type="submit"]:hover {
  opacity: 0.9;
}