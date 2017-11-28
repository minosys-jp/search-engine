<?php
require "./search_engine_ngprob.php";

$atitle = [];
$acontent = [];
$words = "";
if (isset($_POST['words'])) {
  $words = $_POST['words'];
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=10.0, user-scalable=yes" />
<link rel="shortcut icon" href="https://www.teqstock.tokyo/favicon.png">
<link rel="stylesheet" type="text/css" href="https://www.teqstock.tokyo/index.css">

<title>TeqStock.tokyo の検索結果</title>
</head>
<body>
<h1 class="teqstock">
  TeqStock.tokyo ページ検索結果
</h1>

<table>
  <tr>
    <td><a class="menu" href="./">ホーム</a></td>
    <td><a class="menu" href="aboutus.html">TeqStock.tokyo について</a></td>
    <td><a class="menu" href="stock.html">技術置き場</a></td>
    <td><a class="menu" href="blog/">運営ブログ</a></td>
    <td><a class="menu" href="contactus.php">お問い合わせ</a></td>
  </tr>
</table><hr />
TeqStock.tokyo ページの検索結果（運営ブログ除く）<p />

<?php if ($_POST['algo'] == '0') { ?>
単語 &quot;<?php echo htmlspecialchars($words); ?>&quot; を含む記事の一覧<p />
<?php } else { ?>
単語 &quot;<?php echo htmlspecialchars($words); ?>&quot; から連想される記事の一覧<p />
<?php } ?>

<?php echo search($words); ?>

<hr />
<I>Copyright (c) 2017-2018 by TeqStock.tokyo</I>
</body>
</html>
