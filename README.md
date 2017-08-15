# Fun2vec
興味・関心・趣味ベクトル  

### モデル精度確認  
引数は何個でも指定可能  
引数に指定した興味・関心・趣味ベクトルが足しあわされた結果を出力
```bash
$ python word2vec.py 機械学習 ビール アニメ
```

### コマンド使い方     
コマンド一覧取得
```bash
$ python manage.py
```
コマンド実行例
```bash
$ python manage.py word2vec create_model
```

|親コマンド|子コマンド|説明|
|---|---|---|
|db|init_db|全てのテーブルを新規作成します|
|util|encrypt|秘密情報(secrets.yml)を暗号化します(秘密情報を編集した後暗号化するのに使用)|
|util|decrypt_dump|秘密情報(secrets.yml)を復号化します(秘密情報を編集するのに使用)|
|twitter|scrape|TwitterプロフィールデータをTwitter APIを叩いて収集します|
|word2vec|create_model|Twitterプロフィールデータを形態素解析し、分かち書きした後word2vecモデルを新規作成します|

### 環境構築  
・MySQLインストール  
・python3インストール  
・MeCabインストール  
・python moduleインストール
```bash
$ pip install -r requirements.txt
```

### 秘密情報のパスワード  
秘密情報を暗号化・復号化するにはパスワードが必要です。  
```bash
$ export FUN2VEC_SECRET_PASSWORD=xxxxx
```
パスワードがわからない方は @maomao905 まで  

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
