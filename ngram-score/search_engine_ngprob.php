<?php
function mbOrd($x) {
  $x = unpack('Nx', mb_convert_encoding($x, 'UCS-4BE', 'UTF-8'));
  return $x['x'];
}

function mkhash($c1, $c2) {
  $x1 = mbOrd($c1);
  $x2 = mbOrd($c2);
  return ($x1 & 255) ^ (($x2 + 11) & 255);
}

function init() {
  // ハッシュテーブルを読み込み
  $h1 = [];
  $f = fopen("search_ngprob_hash.bin", "rb");
  for ($i = 0; $i < 256; ++$i) {
    $r = fread($f, 4);
    $ra = unpack("Vhash", $r);
    $h1[$i] = $ra["hash"];
  }
  fclose($f);
  return $h1;
}

function engine($h1, $words) {
  $result = [];
  $sw = explode(" ", $words);
  for ($i = 0; $i < count($sw); ++$i) {
    $s = $sw[$i];
    $result = engine1($h1, $s, $result);
  }
  return $result;
}

function engine1($h1, $s, $result) {
  $c2 = '';
  $h2 = fopen("search_ngprob_classify.bin", "rb");
  $slen = mb_strlen($s);
  for ($i = 0; $i < $slen; ++$i) {
    $c1 = $c2;
    $c2 = mb_substr($s, $i, 1);
    if ($c1 == '') {
      continue;
    }
    $h12 = mkhash($c1, $c2);
    if (!isset($h1[$h12])) {
      continue;
    }
    $offset = $h1[$h12];
    fseek($h2, $offset, SEEK_SET);
    $len = unpack('Vlen', fread($h2, 4));
    while ($len['len'] > 0) {
      $lenItem = $len['len'] - 12;
      $r1 = fread($h2, 4);
      $r2 = fread($h2, 4);
      $x1 = unpack('Vx1', $r1);
      $x2 = unpack('Vx2', $r2);
      if ($x1['x1'] == mbOrd($c1) && $x2['x2'] == mbOrd($c2)) {
        while($lenItem > 0) {
          $lenItem -= 8;
          $aoffset = unpack('Voffset', fread($h2, 4));
          $prob = unpack('fprob', fread($h2, 4));
          if (isset($result[$aoffset['offset']])) {
            $result[$aoffset['offset']] += $prob['prob'];
          } else {
            $result[$aoffset['offset']] = $prob['prob'];
            $r = TRUE;	// 有効な値を含む
          }
        }
      } else {
        fseek($h2, $lenItem, SEEK_CUR);
      }
      // trailer は読み飛ばす
      fseek($h2, 4, SEEK_CUR);
      $len = unpack('Vlen', fread($h2, 4));
    }
  }
  fclose($h2);
  return $result;
}

function readText($h3) {
  $len = unpack('vlen', fread($h3, 2));
  $r = fread($h3, $len['len']);
  return $r;
}

function search($s) {
  $h = init();
  $result = engine($h, $s);
  arsort($result);
  $r = "";
  $h3 = fopen("search_ngprob_docs.bin", "rb");
  foreach ($result as $key => $value) {
    if ($value < 1e-8) {
      break;
    }
    fseek($h3, $key);
    $link = readText($h3);
    if ($link == "/") {
      $link = "./";
    }
    $title = readText($h3);
    $body = readText($h3);

    $div = "<div>";
    $div .= sprintf("<h4><a href='%s'>%s</a> (score:%.8f)</h4>\r\n", $link, $title, $value);
    $div .= "</div>\r\n";
    $r .= $div;
  }
  fclose($h3);
  return $r;
}

?>
