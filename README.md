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
- Twitter profileをAPIから取得(600万件)

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

### モデル精度確認  
引数は何個でも指定可能  
引数に指定した興味・関心・趣味ベクトルが足しあわされた結果を出力  
※ ただし最新のモデルはGCSに保存しておりリポジトリにはない
```bash
$ python model.py -m fun2vec
words> 機械学習　アニメ　ビール
```

### コマンド使い方     
コマンド一覧取得
```bash
$ python manage.py
```
コマンド実行例
```bash
$ python manage.py model create_fun2vec
```

### 環境構築  
・MySQLインストール  
```bash
#テーブル作成
$ python manage.py db init_db
```
・Python3インストール (Python3.6)  
・MeCab + ipadic-neologd インストール  
・Python moduleインストール
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
