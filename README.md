# Fun2vec
興味・関心・趣味ベクトル  
この人は〇〇が好きで〇〇が好きであると〇〇が好きである可能性が高い  
そこには関係性があるはずでその関係性がわかったら面白い  

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
|util|encrypt|秘密情報(secrets.yml)を暗号化します(秘密情報を編集した後暗号化するのに使用)|
|util|decrypt_dump|秘密情報(secrets.yml)を復号化します(秘密情報を編集するのに使用)|
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

### 秘密情報のパスワード  
秘密情報を暗号化・復号化するにはパスワードが必要です。  
```bash
$ export FUN2VEC_SECRET_PASSWORD=xxxxx
```

### テスト
実行例
```bash
$ python -m unittest tests.test_corpus
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
