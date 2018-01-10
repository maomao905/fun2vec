## Fun2vec
Fun2vec is word2vec vector about hobbies and interest.  
Suggest next possible funs from the current your interests.  

### Usage
Tweet `#おすすめの趣味を教えて xxx`  (xxx are current your hobbies or interests)        
Bot will reply and suggest hobbies or funs 
```
ex)
User: #おすすめの趣味を教えて 麻雀 酒 研究 読書 漫画
Bot: おすすめの趣味は順番に、将棋/TVゲーム/天体観測/ヒトカラ/サイクリング/推理小説/ビリヤード/ボードゲーム/ボルダリング/クロスバイク
```

### Data Source
Twitter profiles of 6 million users (mainly Japanese)

### Preprocessing
0. Create Dictionary [new_word.csv](data/dictionary/new_word.csv) + [close_word.csv](data/dictionary/close_word.csv) + [close_word_original.csv](data/dictionary/close_word_original.csv) 
1. Morphological Analysis [morpheme.py](morpheme.py)
2. Word Normalization [word.py](word.py)
3. Ignore stopwords [stop_words.txt](data/dictionary/stop_words.txt)

### Create Model  
1. Create word2vec from Twitter profiles text  
2. Extract phrases about hobbies and interests from Twitter profiles [corpus_fun2vec.py](corpus/corpus_fun2vec.py#L17#L23)
```
ex) ...Hobbies: Anime/Reading/Movies... -> Extract Anime, Reading, Movies
ex) I love xxx... I am into xxx... My intests are xxx-> Extract xxx
```
3. Create word2vec with the data created by step 2 (called fun2vec)  
4. K-Means Clustering with the data created by step 1  

Final response: get most similar words from fun2vec but exclude words in which cluster input words are clustered, in order not to suggest too close hobbies like (given `running` suggest `swimming`, given `beer` suggest `wine`)

### Test Model  
```bash
$ python model.py -m fun2vec
words> ビリヤード 将棋 ドライブ
```

### Task Commands  
List the available commands
```bash
$ python manage.py
```
ex)
```bash
$ python manage.py model create_fun2vec
```

### Installation  
- Install MySQL  
```bash
# Initialize DB
$ python manage.py db init_db
```
- Python3.6
- MeCab + ipadic-neologd  
- Python module   
```bash
$ pip install -r requirements.txt
```

#### Note  
When you scrape Twitter data, char code error might occur when text includes emoji.
```
Warning: (1366, "Incorrect string value: '\\xF0\\x9F\\x92\\xB8\\xE8\\xB2...' for column 'description' at row 1")
```
Then edit following
```
# /etc/my.cnf
[mysqld]
...
character-set-server=utf8mb4
```
Restart MySQL and check
```
> show variables like "chara%";
```
Might also need the following command  
```
> ALTER TABLE fun.users MODIFY COLUMN description TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```
ref: http://qiita.com/deco/items/bfa125ae45c16811536a
