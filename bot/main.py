import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from model import Model
from cluster import Cluster
from util import load_config, _unpickle, _pickle
from api.twitter import Twitter
import numpy as np
import json
from time import sleep
from word import Word
import logging.config
config = load_config('file')
logging.config.dictConfig(load_config('log'))
_logger = logging.getLogger(__name__)
_tweet_logger = logging.getLogger('tweetlog.' + __name__) # tweet log
# modelは最初に読み込みしておく

# Streaming APIでずっと調べる
# ハッシュタグがあった場合に特定メソッドを実行

# fun2vecで類似度が高いものを取得
# 入力語でのクラスタと同じクラスタにいる結果は除く

def make_word_cluster_label_data():
    """make data that key is word, value is clustered label
    {'将棋': 748, '囲碁': 748,,,,}
    """
    word_label = {}
    word2vec = Model('word2vec')
    clf = Cluster(config['cluster']['kmeans'])
    _pickle(dict(zip(word2vec.vocab, clf.labels)), config['cluster']['labels'])
    _logger.info(f"{len(word2vec.vocab)} word label data saved in {config['cluster']['labels']}")

def get_next_funs(funs, cluster_labels, fun2vec):
    user_funs = [fun for fun in funs if fun in fun2vec.vocab]
    text = ''
    if len(funs) == 0:
        return text
    elif len(funs) < 3:
        text += f'あなたの趣味や興味をなるべく多く入れた方が正確になります。'
    user_labels = list(filter(lambda x: x != None, [cluster_labels.get(fun) for fun in funs]))
    # 入力文と同じクラスタに入るものは除く
    words_without_same_cluster = [word for word, sim in fun2vec.most_similar(funs, topn=50) if cluster_labels.get(word) not in user_labels]
    # さらに結果の中で同じクラスタはまとめて表示
    result = []
    result_cluster_labels = []
    for w in words_without_same_cluster:
        label = cluster_labels.get(w)
        if label not in result_cluster_labels:
            result.append(w)
        result_cluster_labels.append(label)
        if len(result) >= 10:
            break
    text += 'おすすめの趣味は順番に、' + '/'.join(result)
    return text

def main():
    """
    Detect particular hashtag
    """
    _word = Word()
    fun2vec = Model('fun2vec')
    cluster_labels = _unpickle(config['cluster']['labels'])
    __TAG = '#おすすめの趣味を教えて'
    t = Twitter()
    t._logger.info('Requsting to Twitter API...')
    res = t.search(__TAG)
    if res.ok:
        store_users = {}
        for idx, line in enumerate(res.iter_lines(), 1):
            try:
                if line:
                    info = json.loads(line.decode('utf-8'))
                    input_text = info['text'].replace(__TAG, '').strip()
                    # 区切りで入力された場合は形態素解析しない方が正確なのでsplitで分けるだけにする
                    user_funs = input_text.split()
                    user_funs = _word.preprocess(input_text) if len(user_funs) < 3 else user_funs
                    _tweet_logger.info(f"Received from @{info['user']['screen_name']} {user_funs}")
                    text = get_next_funs(user_funs, cluster_labels, fun2vec)
                    if text:
                        t.send(f"@{info['user']['screen_name']} {text}", reply_to=info['id'])
                    _tweet_logger.info(f"Reply to @{info['user']['screen_name']} {text}")
            except Exception as e:
                t._logger.error(e)
                sleep(15*60)
                continue
    else:
        t._logger.error('Requst to Twitter API failed')
        res.raise_for_status()

main()
# if __name__ == '__main__':
#     user_funs = (['麻雀', '酒', '研究', '読書', '漫画'], \
#         ['将棋', 'ビリヤード', 'プログラミング', 'サッカー'], \
#         ['漫画', '小説', '映画', 'テニス', 'カフェ'], \
#         ['ジャニーズ', 'ラジオ', '音楽', '楽器', '本'], \
#         ['ランニング', '映画', '読書'], \
#         ['将棋', 'ビリヤード', 'Netflix'])
#     fun2vec = Model('fun2vec')
#     cluster_labels = _unpickle(config['cluster']['labels'])
#     for _user_funs in user_funs:
#         print('-' * 50)
#         print('今の趣味:', _user_funs)
#         print(get_next_funs(_user_funs, cluster_labels, fun2vec))
