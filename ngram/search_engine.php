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
  $f = fopen("search_hash.bin", "rb");
  for ($i = 0; $i < 256; ++$i) {
    $r = fread($f, 4);
    $ra = unpack("Vhash", $r);
    $h1[$i] = $ra["hash"];
  }
  fclose($f);
  return $h1;
}

function engine($h1, $s) {
  if ($s == '' || mb_strlen($s) < 2) {
    return null;
  }
  $r = null;
  $c2 = '';
  $h2 = fopen("search_classify.bin", "rb");
  $slen = mb_strlen($s);
  for ($i = 0; $i < $slen; ++$i) {
    $c1 = $c2;
    $c2 = mb_substr($s, $i, 1);
    if ($c1 == '') {
      continue;
    }
    $offset = $h1[mkhash($c1, $c2)];
    fseek($h2, $offset, SEEK_SET);
    $len = unpack('Vlen', fread($h2, 4));
    while ($len['len'] > 0) {
      $r1 = fread($h2, 4);
      $r2 = fread($h2, 4);
      $x1 = unpack('Vx1', $r1);
      $x2 = unpack('Vx2', $r2);
      if ($x1['x1'] == mbOrd($c1) && $x2['x2'] == mbOrd($c2)) {
        $itemLen = unpack('Vlen', fread($h2, 4));
        $rnew = [];
        while ($itemLen['len'] > 0) {
          $aoffset = unpack('Voffset', fread($h2, 4));
          $canold = null;
          if ($r != null) {
            if (isset($r[$aoffset['offset']])) {
              $canold = $r[$aoffset['offset']];
            } else {
              fseek($h2, $itemLen['len'], SEEK_CUR);
              $itemLen = unpack('Vlen', fread($h2, 4));
              continue;
            }
          }
          $itemCount = $itemLen['len'] >> 2;
          $candidate = [];
          for ($j = 0; $j < $itemCount; ++$j) {
            $pos = unpack('Vpos', fread($h2, 4));
            if ($r != null) {
              for ($k = 0; $k < count($canold); ++$k) {
                if ($canold[$k] + 1 == $pos['pos']) {
                  $candidate[] = $pos['pos'];
                }
              }
            } else {
              $candidate[] = $pos['pos'];
            }
          }
          $rnew[$aoffset['offset']] = $candidate;
          $itemLen = unpack('Vlen', fread($h2, 4));
        }
        $r = $rnew;
        break;
      } else {
        fseek($h2, $len['len'] - 8, SEEK_CUR);
        if ($r == null) {
          $r = [];
        }
      }
      $len = unpack('Vlen', fread($h2, 4));
    }
  }
  fclose($h2);
  return $r;
}

function readText($h3) {
  $len = unpack('vlen', fread($h3, 2));
  $r = fread($h3, $len['len']);
  return $r;
}

function search($s) {
  $h = init();
  $e = engine($h, $s);
  if (!$e) {
    return "";
  }
  $r = "";
  $h3 = fopen("search_docs.bin", "rb");
  foreach ($e as $key => $value) {
    fseek($h3, $key);
    $link = readText($h3);
    if ($link == "/") {
      $link = "./";
    }
    $title = readText($h3);
    $body = readText($h3);

    $div = "<div>";
    $div .= "<h4><a href='" . $link . "'>" . $title . "</a></h4>";
    foreach ($value as $i => $pos) {
      $xpos = $pos + 1;
      $ppos = $xpos - mb_strlen($s);
      $coff1 = 15;
      $st = $ppos - $coff1;
      if ($st < 0) {
        $st = 0;
        $coff1 = $ppos - $st;
      }
      $part = "";
      if ($coff1 > 0) {
        $part = mb_substr($body, $st, $ppos - $st);
      }
      $part .= "<b><u><i>";
      $part .= mb_substr($body, $ppos, $xpos - $ppos);
      $part .= "</i></u></b>";
      $coff2 = 15;
      $ed = $xpos + $coff2;
      if ($ed > mb_strlen($body)) {
        $ed = mb_strlen($body);
        $coff2 = $ed - $xpos;
      }
      if ($coff2 > 0) {
        $part .= mb_substr($body, $xpos, $ed - $pos);
      }

      $div .= "<div>";
      $div .= $part;
      $div .= "</div>";
    }
    $div .= "</div>\r\n";
    $r .= $div;
  }
  fclose($h3);
  return $r;
}

?>
