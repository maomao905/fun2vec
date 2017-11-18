from sklearn.cluster import MiniBatchKMeans
from model import Model
from sklearn.externals import joblib
import numpy as np
from collections import defaultdict
from functools import cmp_to_key
from gensim.models import LdaModel
from gensim import corpora
import pickle, gzip
from util import load_config
import logging

logging.config.dictConfig(load_config('log'))
logger = logging.getLogger(__name__)

config = load_config('file')

FILE_FUN2VEC = 'data/fun.model'
FILE_KMEANS = 'data/kmeans_fun.pkl'

def cluster_funs_by_kmeans(K):
    """
    興味で同じような興味は塊が多すぎて、同じような興味が出てくるのでそれを防ぐため、clusteringする
    current vocab_size => len(model.wv.vocab) 23402
    """
    embeddings = load_model('word2vec').wv.syn0norm
    clf = MiniBatchKMeans(n_clusters=K, batch_size=500, init_size=10000, random_state=0)
    clf.fit(embeddings)
    save(clf, FILE_KMEANS)

def cluster_hierarchical():
    """
    metric choices
    ref : https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.pdist.html
    """
    model = load_model('word2vec').wv
    from  scipy.spatial.distance  import pdist
    from scipy.cluster.hierarchy import linkage, dendrogram
    from matplotlib import pyplot as plt

    TEST_NUM = 100

    l = linkage(model.syn0norm[:TEST_NUM], method='complete', metric='cosine')

    # plt.figure(figsize=(25, 10))
    # plt.title('Hierarchical Clustering Dendrogram')
    # plt.ylabel('word')
    # plt.xlabel('distance')

    dendrogram(
        l,
        leaf_font_size=8.,  # font size for the x axis labels
        leaf_label_func=lambda v: str(model.index2word[:TEST_NUM][v])
    )
    plt.show()

def check(words):
    clf = joblib.load(FILE_KMEANS)
    model = load_model('word2vec').wv
    X = [model[word] for word in words]
    centroids = clf.predict(X)
    for w, centroid in zip(words, centroids):
        group_indices = np.argwhere(clf.labels_ == centroid)
        group_words = [model.index2word[idx] for idx in group_indices.flatten()]
        print('-' * 100)
        print(f'{w}と同じクラスタにいるワードは')
        print(group_words)

def save(clf, file_path):
    joblib.dump(clf, file_path, compress=True)

def cluster_funs(_model, funs):
    """
    Cluster funs to make each fun distinctive
    funs: ['パソコン', 'スマホ', 'タブレット', '読書']
    cluster key: most_similarで0.8以上の単語, score: cos類似度合計 group: most_similarした単語(funs)
    cluster: {
        'タブレット': {'score': 2.5830405950546265, 'group': {'スマホ', 'パソコン', 'タブレット'},
        'スマホ':     {'score': 2.533282995223999,  'group': {'パソコン', 'タブレット', 'スマホ'},
        'パソコン':   {'score': 2.5194380283355713, 'group': {'パソコン', 'タブレット', 'スマホ'},
        '映画鑑賞':   {'score': 0.8885858058929443, 'group': {'読書'}
    }
    => scoreが一番高いものを採用しgroup(スマホ・パソコン)を'タブレット'にclusterする
    (ただし、scoreが同じ場合は頻度が高い方にclusterする)
    return: ['タブレット', '読書']
    """
    # 複数ない場合はクラスタリングする必要がない
    if len(funs) < 2:
        return funs
    funs = set(funs)
    cluster = defaultdict(lambda: dict(score=0, group=set()))
    except_funs = set()
    for fun in funs:
        try:
            res = _model.most_similar(positive=fun,topn=20)
        except KeyError:
            except_funs.add(fun)
            continue
        for word, sim in res:
            if sim < 0.6:
                continue
            # 5桁以上同じ場合は単語の頻度を優先させた方がよさそう
            sim = round(sim, 5)
            cluster[word]['score'] += sim
            cluster[word]['group'].add(fun)
            # word自身がfunsにすでに入っている場合はその分一回カウントされないので、ここでカウント
            if word in funs and word not in cluster[word]['group']:
                cluster[word]['score'] += sim
                cluster[word]['group'].add(word)
    # 頻度が少なすぎるものは除く
    funs -= except_funs

    def _compare(f1, f2):
        """
        score(cos類似度の合計)が高いもの順にソートするが、
        同一scoreの場合は単語の頻度が高いを方を優先する
        """
        if f1[1]['score'] == f2[1]['score']:
            return 1 if _model.wv.vocab[f1[0]].count > _model.wv.vocab[f2[0]].count else -1
        else:
            return 1 if f1[1]['score'] > f2[1]['score'] else -1

    cluster = sorted(cluster.items(), key=cmp_to_key(_compare), reverse=True)
    _clustered_funs = set()
    for word, word_cluster in cluster:
        # すでにクラスタリングされたwordは扱わない
        if word in _clustered_funs:
            continue
        # groupに２つ以上要素がない場合はクラスタリングする必要がないので終了
        if len(word_cluster['group']-_clustered_funs) < 2:
            break
        # クラスタリング
        funs -= word_cluster['group']
        funs.add(word)
        # クラスタリングされたものを記録しておく
        _clustered_funs.update(word_cluster['group'])
        # さらにwordはクラスタリングする可能性があるので残す
        _clustered_funs.discard(word)

    return list(funs)

def find_topic():
    """
    LdaModel params
        passes: Number of passes through the entire corpus
        chunk_size: how many documents to load into memory
        update_every: number of chunks to process prior to moving onto the M step of EM
    """
    with gzip.open(config['fun2vec']['corpus'], 'rb') as f:
        words = pickle.load(f)
    # 辞書作成
    dictionary = corpora.Dictionary(words)
    dictionary.filter_extremes(no_below=30, no_above=0.3)

    # コーパスを作成
    corpus = [dictionary.doc2bow(_words) for _words in words]
    # corpora.MmCorpus.serialize('cop.mm', corpus)
    lda = LdaModel(corpus, num_topics=10, chunksize=10000, update_every=2, id2word=dictionary)
    lda.save(config['topic_model'])
    pprint(lda.show_topics(num_words=20))

if __name__ == '__main__':
    from pprint import pprint
    # cluster_funs_by_kmeans(300)
    check(['将棋', 'サッカー', '野球', 'ロッテ'])
    # cluster_hierarchical()
