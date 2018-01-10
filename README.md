# Fun2vec
興味・関心・趣味ベクトル  
この人は〇〇が好きで〇〇が好きであると〇〇が好きである可能性が高い  
そこには関係性があるはずでその関係性がわかったら面白い  

### How to use
Twitterで
`#おすすめの趣味を教えて xxx` とつぶやくとおすすめの趣味が返ってくる  
例)   
```
U: #おすすめの趣味を教えて ラーメン 野球 読書 映画
B: おすすめの趣味は順番に、食べ歩き/球技/推理小説/ボルダリング/ビリヤード/クロスバイク/スイーツ/ヒトカラ/将棋/梅酒
```

### データ収集
- Twitter profileをAPIから取得
- Twitterで誰が誰をフォローしているかの情報をAPIから取得
- フォロー関係から興味・趣味データを拡大していく

### 前処理
0. 辞書構築 [new_word.csv](data/dictionary/new_word.csv) + [close_word.csv](data/dictionary/close_word.csv) + [close_word_original.csv](data/dictionary/close_word_original.csv) を使って独自辞書を作成
1. 形態素解析 [morpheme.py](morpheme.py)
2. 単語を正規化 [word.py](word.py)
3. ストップワードは無視 [stop_words.txt](data/stop_words.txt)

### close word作り方  
- 並列なものだけにする。  
ok 俳優,俳優さん  
bad 俳優,若手俳優  
bad ワイン, 白ワイン  
ただし、二つの後の意味の違いが意味をなさないようなものはok  
ok 代表,副代表

### モデル作成
- word2vec corpus作成  
DBから全profile取得して形態素解析してcorpus保存
- fun2vec corpus作成  
DBからprofile取得して興味部分を抽出して保存
- word2vec model作成  
- fun2vec corpus作成  
この際にuser_idを保存する必要がある  
- fun2vec clustered corpus作成  
fun2vecの興味をdistinctiveにするために、fun2vecのcorpusをword2vecのmost_similarで似た興味をグループ化  
- fun2vec clustered model作成

### モデル精度確認  
引数は何個でも指定可能  
引数に指定した興味・関心・趣味ベクトルが足しあわされた結果を出力
```bash
$ python fun2vec.py
words> 機械学習　アニメ　ビール
```

### コマンド使い方     
コマンド一覧取得
```bash
$ python manage.py
```
コマンド実行例
```bash
$ python manage.py fun2vec create_fun2vec_model
```

|親コマンド|子コマンド|説明|
|---|---|---|
|db|init_db|全てのテーブルを新規作成します|
|twitter|scrape|TwitterプロフィールデータをTwitter APIを叩いて収集します|
|fun2vec|create_word2vec|Twitterプロフィールデータを形態素解析し、分かち書きした後word2vecモデルを新規作成します|
|fun2vec|create_fun2vec|既存のword2vec, 辞書とコーパスを使い最適な興味ベクトルを作る|
|fun2vec|check_vocab|vocabraryにどのような単語があるか調べる時に使う|

### 環境構築  
・MySQLインストール  
```bash
#テーブル作成
$ python manage.py db init_db
```
・python3インストール  
・MeCab + ipadic-neologd インストール  
・python moduleインストール
```bash
$ pip install -r requirements.txt
```

### Mecabオリジナル辞書コンパイル
```bash
$ /usr/local/Cellar/mecab/0.996/libexec/mecab/mecab-dict-index \
-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd \
-u data/dictionary/original_dic.dic \
-f utf-8 \
-t utf-8 \
data/dictionary/original_dic.csv
```

### 秘密情報のパスワード  
秘密情報を暗号化・復号化するにはパスワードが必要です。  
```bash
$ export FUN2VEC_SECRET_PASSWORD=xxxxx
```

### テスト
実行例
```bash
$ python -m unittest tests.test_corpus
$ py.test <test_file>
```

#### 補足  
Twitterデータscraping時に以下のようなエラー(絵文字が入っていると文字コードエラーになる)になった場合
```
Warning: (1366, "Incorrect string value: '\\xF0\\x9F\\x92\\xB8\\xE8\\xB2...' for column 'description' at row 1")
```
以下を編集
```
# /etc/my.cnf
[mysqld]
...
character-set-server=utf8mb4
```
MySQL再起動して確認
```
> show variables like "chara%";
```
DB文字コードを修正してもテーブルの文字コードがutf8のままの場合、そちらが優先されてしまうので、
テーブル文字コードも修正
```
> ALTER TABLE fun.users MODIFY COLUMN description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```
ref: http://qiita.com/deco/items/bfa125ae45c16811536a
