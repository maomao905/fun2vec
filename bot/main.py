import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from model import Model
from cluster import Cluster
from util import load_config
from api.twitter import Twitter
import numpy as np
import json
from time import sleep
config = load_config('file')
# modelは最初に読み込みしておく

# Streaming APIでずっと調べる
# ハッシュタグがあった場合に特定メソッドを実行

# fun2vecで類似度が高いものを取得
# 入力語でのクラスタと同じクラスタにいる結果は除く

# 返却
fun2vec = Model('fun2vec')
word2vec = Model('word2vec')
clf = Cluster(config['cluster']['kmeans'])
def get_cluster_words(words):
    cluster_words = []
    X = word2vec.get_vectors(words)[1]
    centroids = clf.predict(X)
    for w, centroid in zip(words, centroids):
        group_indices = np.argwhere(clf.labels == centroid)
        cluster_words.extend([word2vec.vocab[idx] for idx in group_indices.flatten()])
    return cluster_words

def main():
    """
    Detect particular hashtag
    """

    __TAG = '#趣味を教えて'
    t = Twitter()
    t._logger.info('Requsting to Twitter API...')
    res = t.search(__TAG)
    if res.ok:
        store_users = {}
        for idx, line in enumerate(res.iter_lines(), 1):
            try:
                if line:
                    info = json.loads(line.decode('utf-8'))
                    user_funs = info['text'].replace(__TAG, '').strip().split()
                    user_funs = [fun for fun in user_funs if fun in fun2vec.vocab]
                    text = ''
                    if len(user_funs) == 0:
                        continue
                    elif len(user_funs) < 3:
                        text += f'あなたの趣味や興味をなるべく多く入れたほうが正確になります。'
                    cluster_words = get_cluster_words(user_funs)
                    result = [word for word, sim in fun2vec.most_similar(user_funs, topn=50) if word not in cluster_words]
                    result = result[:10]
                    text += 'あなたに合う趣味は順番に、' + '/'.join(result)
                    t.send(f"@{info['user']['screen_name']} {text}", reply_to=info['id'])
            except Exception as e:
                t._logger.error(e)
                sleep(15*60)
                continue
    else:
        t._logger.error('Requst to Twitter API failed')
        res.raise_for_status()

if __name__ == '__main__':
    main()
