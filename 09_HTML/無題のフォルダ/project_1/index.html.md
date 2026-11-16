<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>多色スタイルのサンプルページ</title>
  <!-- 同じフォルダ内の style.css を読み込み -->
  <link rel="stylesheet" href="style.css">
</head>
<body>

  <h1>多色スタイルのサンプル</h1>
  <p>外部CSSファイル（style.css）からスタイルを読み込み、デザインを整えたドキュメントです。</p>

  <h2 class="section-link">リンクと画像</h2>
  <p><a href="https://example.com" target="_blank" rel="noopener noreferrer">外部サイトへのリンク</a></p>
  <img src="https://via.placeholder.com/300x150/0284c7/ffffff?text=Sample+Image" alt="サンプル画像" width="300" height="150">

  <h2 class="section-todo">ToDoリスト</h2>
  <ul>
    <li>HTMLの構造を理解する</li>
    <li>タグの役割を覚える</li>
    <li>外部CSSファイルを連携する</li>
  </ul>

  <h2 class="section-table">料金表</h2>
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

  <h2 class="section-form">お問い合わせフォーム</h2>
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

    <button type="submit">送信する</button>
  </form>

</body>
</html>




