
`<head>` 内に `<style>` タグを配置し、全体の余白、フォント、配色、テーブル、フォームのデザインを整えた完全なコードです。

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
      <tr>
        <td>特別</td>
        <td>3,000円</td>
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
