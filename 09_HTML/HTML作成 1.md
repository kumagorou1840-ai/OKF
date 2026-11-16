
HTMLドキュメントの基本構造
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>ページのタイトル</title>
</head>
<body>
  <h1>見出し</h1>
  <p>ここに本文を書きます。</p>
</body>
</html>



<!-- 通常のリンク -->
<a href="https://example.com">サンプルサイトへ</a>

<!-- 別タブで開くリンク -->
<a href="https://example.com" target="_blank" rel="noopener noreferrer">新しいタブで開く</a>

<!-- 相対パスまたはURLを指定 -->
<img src="images/sample.jpg" alt="サンプルの写真" width="300">


<a href="https://example.com">
  <img src="images/banner.jpg" alt="バナー画像">
</a>


<ul>
  <li>りんご</li>
  <li>バナナ</li>
  <li>オレンジ</li>
</ul>

<ol>
  <li>お湯を沸かす</li>
  <li>ティーバッグを入れる</li>
  <li>3分待つ</li>
</ol>

<ul>
  <li>果物
    <ul>
      <li>りんご</li>
      <li>みかん</li>
    </ul>
  </li>
  <li>野菜</li>
</ul>

<table border="1">
  <tr>
    <th>商品名</th>
    <th>価格</th>
  </tr>
  <tr>
    <td>りんご</td>
    <td>150円</td>
  </tr>
  <tr>
    <td>バナナ</td>
    <td>200円</td>
  </tr>
</table>

行数が増える実用的なテーブルでは、ヘッダーと本体をグループ分けして記述します。
<table border="1">
  <thead>
    <tr>
      <th>番号</th>
      <th>品名</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>ノート</td>
    </tr>
    <tr>
      <td>2</td>
      <td>ペン</td>
    </tr>
  </tbody>
</table>

フォームは全体を `<form>` で囲み、その中に各種入力部品（`<input>`, `<textarea>` など）や送信ボタンを配置します。
<form action="/submit" method="post">
  <!-- 1行テキスト入力 -->
  <div>
    <label for="username">お名前:</label>
    <input type="text" id="username" name="username" placeholder="山田太郎" required>
  </div>

  <!-- メールアドレス入力 -->
  <div>
    <label for="email">メールアドレス:</label>
    <input type="email" id="email" name="email" required>
  </div>

  <!-- 複数行テキスト入力 -->
  <div>
    <label for="message">お問い合わせ内容:</label>
    <textarea id="message" name="message" rows="4"></textarea>
  </div>

  <!-- 送信ボタン -->
  <button type="submit">送信する</button>
</form>


プルダウン（ドロップダウン）選択メニューは、`<select>` タグの中に `<option>` タグを並べて作成します。

<label for="fruits">好きな果物を選択：</label>
<select id="fruits" name="selected_fruit">
  <option value="">選択してください</option>
  <option value="apple">りんご</option>
  <option value="orange" selected>みかん</option>
  <option value="banana">バナナ</option>
</select>


選択肢が多い場合は、`<optgroup>` でカテゴリ分けできます。
<select name="drink">
  <optgroup label="温かい飲み物">
    <option value="hot_coffee">ホットコーヒー</option>
    <option value="tea">紅茶</option>
  </optgroup>
  <optgroup label="冷たい飲み物">
    <option value="ice_coffee">アイスコーヒー</option>
    <option value="juice">オレンジジュース</option>
  </optgroup>
</select>


1. ラジオボタン（単一選択）
同じグループにする項目の `name` 属性を**同じ名前に統一**することで、どれか1つしか選べない動作になります。

<p>性別を選択してください：</p>

<input type="radio" id="male" name="gender" value="male">
<label for="male">男性</label>

<input type="radio" id="female" name="gender" value="female">
<label for="female">女性</label>

<input type="radio" id="other" name="gender" value="other" checked>
<label for="other">その他（初期選択）</label>


### 2. チェックボックス（複数選択可）

複数選択できるため、基本は項目ごとに別の `name` を割り当てるか、同一カテゴリとして配列風に扱います。
<p>興味のある分野（複数選択可）：</p>

<input type="checkbox" id="tech" name="interests" value="tech" checked>
<label for="tech">テクノロジー（初期選択）</label>

<input type="checkbox" id="sports" name="interests" value="sports">
<label for="sports">スポーツ</label>

<input type="checkbox" id="music" name="interests" value="music">
<label for="music">音楽</label>


### 1. 基本的な読み込み手順

同じフォルダに `index.html` と `style.css` を配置する場合の構成例です。

<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>ページタイトル</title>
  <!-- CSSファイルの読み込み -->
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h1>スタイル適用のテスト</h1>
  <p>CSSが連携されていると色や文字サイズが変わります。</p>
</body>
</html>


h1 {
  color: #2b6cb0;
}

p {
  font-size: 16px;
  line-height: 1.6;
}

### 3. フォルダを分ける場合（推奨構成）

`css` フォルダ内に `style.css` を格納した場合は、相対パスでフォルダ名を指定します。

<link rel="stylesheet" href="css/style.css">


###########################################################

<article>
  <h2>自己紹介</h2>
  <img src="my-photo.jpg" alt="私の写真">
  <p>こんにちは！Web制作を勉強中の<strong>なると</strong>です。</p>
  
  <h3>好きなものリスト</h3>
  <ul>
    <li>プログラミング</li>
    <li>カフェ巡り</li>
    <li>読書</li>
  </ul>

  <a href="https://example.com">ポートフォリオを見る</a>
</article>

##############################################################

```html
<p>これは <span class="highlight">重要な部分</span> です。</p>
```

```css
.highlight {
  color: #e91e63;
}
```

############################################################

<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>デザインを整えたHTMLサンプル</title>
  <style>
    /* 全体の基本設定 */
    body {
      font-family: sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 680px;
      margin: 40px auto;
      padding: 0 20px;
      background-color: #f9f9f9;
    }

    /* 見出し */
    h1 {
      border-bottom: 2px solid #2563eb;
      padding-bottom: 8px;
      color: #1e293b;
    }

    h2 {
      margin-top: 32px;
      font-size: 1.25rem;
      color: #334155;
    }

    /* テーブル */
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
      background-color: #fff;
    }

    th, td {
      border: 1px solid #cbd5e1;
      padding: 10px 12px;
      text-align: left;
    }

    th {
      background-color: #f1f5f9;
      font-weight: 600;
    }

    /* フォーム */
    form {
      background-color: #fff;
      padding: 20px;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
    }

    .form-group {
      margin-bottom: 16px;
    }

    label {
      display: inline-block;
      margin-bottom: 4px;
      font-weight: 500;
    }

    input[type="text"],
    select {
      width: 100%;
      padding: 8px;
      border: 1px solid #cbd5e1;
      border-radius: 4px;
      box-sizing: border-box;
    }

    /* ボタン */
    button {
      background-color: #2563eb;
      color: #fff;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      font-size: 1rem;
      cursor: pointer;
    }

    button:hover {
      background-color: #1d4ed8;
    }
  </style>
</head>
<body>

  <h1>サンプルページへようこそ</h1>
  <p>CSSを埋め込み、読みやすさと操作性を整えたドキュメントです。</p>

  <h2>リンクと画像</h2>
  <p><a href="https://example.com" target="_blank" rel="noopener noreferrer">外部サイトへのリンク</a></p>
  <img src="https://via.placeholder.com/300x150" alt="サンプル画像" width="300" height="150">

  <h2>ToDoリスト</h2>
  <ul>
    <li>HTMLの構造を理解する</li>
    <li>タグの役割を覚える</li>
    <li>フォームを作成する</li>
  </ul>

  <h2>料金表</h2>
  <table>
    <thead>
      <tr>
        <th>プラン名</th>
        <th>月額料金</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>スタンダード</td>
        <td>1,000円</td>
      </tr>
      <tr>
        <td>プレミアム</td>
        <td>2,000円</td>
      </tr>
    </tbody>
  </table>

  <h2>お問い合わせフォーム</h2>
  <form action="#" method="post">
    <div class="form-group">
      <label for="name">お名前：</label>
      <input type="text" id="name" name="name" required>
    </div>

    <div class="form-group">
      <label for="category">種別：</label>
      <select id="category" name="category">
        <option value="general">一般的な質問</option>
        <option value="support">サポート</option>
      </select>
    </div>

    <div class="form-group">
      <label><input type="radio" name="reply" value="yes" checked> 返信を希望する</label>
      <label style="margin-left: 12px;"><input type="radio" name="reply" value="no"> 返信不要</label>
    </div>

    <button type="submit">送信</button>
  </form>

</body>
</html>


