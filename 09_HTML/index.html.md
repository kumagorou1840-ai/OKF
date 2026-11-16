<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>HTMLサンプルページ</title>
</head>
<body>

  <!-- ヘッダー・見出し -->
  <h1>サンプルページへようこそ</h1>
  <p>これはHTMLの基本要素をまとめたドキュメントです。</p>

  <!-- リンクと画像 -->
  <h2>リンクと画像</h2>
  <p><a href="https://example.com" target="_blank" rel="noopener noreferrer">外部サイトへのリンク</a></p>
  <img src="https://via.placeholder.com/300x150" alt="サンプル画像" width="300" height="150">

  <!-- 箇条書きリスト -->
  <h2>ToDoリスト</h2>
  <ul>
    <li>HTMLの構造を理解する</li>
    <li>タグの役割を覚える</li>
    <li>フォームを作成する</li>
  </ul>

  <!-- テーブル -->
  <h2>料金表</h2>
  <table border="1">
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

  <!-- 入力フォーム -->
  <h2>お問い合わせフォーム</h2>
  <form action="#" method="post">
    <div>
      <label for="name">お名前：</label>
      <input type="text" id="name" name="name" required>
    </div>
    <br>
    <div>
      <label for="category">種別：</label>
      <select id="category" name="category">
        <option value="general">一般的な質問</option>
        <option value="support">サポート</option>
      </select>
    </div>
    <br>
    <div>
      <label><input type="radio" name="reply" value="yes" checked> 返信を希望する</label>
      <label><input type="radio" name="reply" value="no"> 返信不要</label>
    </div>
    <br>
    <div>
      <button type="submit">送信</button>
    </div>
  </form>

</body>
</html>
