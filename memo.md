・興味の内容がめちゃくちゃ問題
=> 頻度で足切りしようと思ったが頻度にかかわらずめちゃくちゃっぽい
=> jumanでドメイン獲得できるからそれでやろうとも思ったがダメ

・gensim util cossimilarity => cos類似度がわかる(word_vectors.similarity('woman', 'man')でもわかる)
・gensim math unitvec => vectorをunit lengthにする

・一旦most_similarで出てきたワードのcos類似度を見てみて本当にあっているかを見る
・word2vecはtrainしないときはuse_norm(normalizeされた方を使った方がよい => computationally efficient)

・sorted_vocabはdefaultで1になっている。word2vecを作ってmost_similarでrestrict_orderする
・目検でチェックして良さそうなワードを選びそのmost_similarを入れる

・１文字は省いてもいいかも => 酒・娘とかあるので省かない方がよい。

・重心が間違っているのを修正

・固有名詞はいらないかも、一般とサ変接続の名詞だけでもいけるような気がしてきた => やっぱりいる
・普通のmecabを使ってみたが、
corpusの中身が若干普通すぎてつまらない。やはりneologeに戻すか。そして固有名詞も入れるか
word2vecとfun2vecの結果がほぼ同じになってしまった。なぜ？たぶん、形態素解析でより細かく区切られるので、文章の文脈というよりは
普通に隣にあるもの同士かどうかの方が重要になってしまう。

・most_similarは結局どれか１つに強く反応してしまう、中間ではないなあ、いやよくみたらうまくできているかも
結局補正をしたとしても同じようなことになるor３つ以上の場合、補正するのも大変だからこのままでもいい気がしてきた。
カメラ+相撲 => 写真撮影

・単語ベクトルメモ model.wv.word_vec('サッカー', use_norm=True) use_normでL2normされているのでcomputationally efficient
・model.similar_by_vector ベクトルを入力すると類似ワードtopn件が返ってくる
・euclid距離メモ np.linalg.norm(vec1-vec2)

・なんかこうビリヤードでダーツとでてくるよりは、パズルとエンジニアとか潜在的な要素が反映されないと意味がない
やはりVの数はある程度ないとダメ
most_similarで拡張して3000までしたがそれを1万とかにする？
・同じ意味の単語をまとめる
プログラマー プログラミングなど
・visualizeする
・window_sizeを20とかにして全部やると全部の趣味から予測するとベクトル平均してるだけだからめちゃくちゃになるんじゃない？
本当はrandomに５つとかとってやるのがいいけど

198486/910000 profiles
正規表現で通ったものにword2vecをかける
保守的にやってみるのもありかも
・feature[6]とfeature[7]を一緒にする ex 漫画 マンガ, Pokemon! ポケモン => 頻度が多い方を採用
・１文字も全部消す
・学問と趣味と仕事をわけてそれぞれを当てにいくでもいいかもな
・地名も全部省くかあ
・類義語をまとめる 映画鑑賞、映画 ngramかな
カメラ・写真撮影 お肉。=> mecabを直す必要
・人名全部省くかあ 徳永英明
柴田淳
忌野清志郎
RHYMESTER
玉置浩二
・例え出力が妥当なものだとしても、それを見ても何も思わない問題
・カメラで写真撮影がでてきても何も思わない
野球でプロ野球が出てきても何も思わない
つまりDomain -> SubDomainが出てくるということは、野球の近くにプロ野球があるために学習されてしまっている。
word2vecでmost_similarで共通部分は一つにまとめては？
sim順に並べる
Counterでcountが2以上になったものを採用
同じ場合は頻度が多い方を採用
２パターン
A -> B
B -> A
-------
A -> C
B -> C
most_similar_cosmul
3CosMul(簡単に言うとaddをやめてmultiplyしている)
https://github.com/RaRe-Technologies/gensim/blob/b818c91c698b4a149c55455b88953714d1701031/gensim/models/keyedvectors.py#L492
計算コストは上がりそう 全部multiplyしている200次元
we propose switching from
an additive to a multiplicative combination
This is equivalent to taking the logarithm of each
term before summation, thus amplifying the differences
between small quantities and reducing
the differences between larger ones.
http://www.aclweb.org/anthology/W14-1618
=> そこまで結果は変わらない(simの少数２桁目が変わるぐらい)し、同じような意味の語の差を出したいというよりはまとめたいので今は使わない
・most_similarでclusteringした(cluster_funs)が、そこまでまとまらない
-> 同じようなfunsが少ない場合もある。
-> いやでも結果似たようなのがでているから
-> どうすればいいんだろう
topic modelを試したがうまくいかず
そもそも趣味と趣味の潜在的な関係性とかはもっとデータが必要なのかも10倍くらい
