from sklearn.cluster import MiniBatchKMeans
from fun2vec import load_model
from sklearn.externals import joblib
import numpy as np
from collections import defaultdict
from functools import cmp_to_key

FILE_FUN2VEC = 'data/fun.model'
FILE_KMEANS = 'data/kmeans_fun.pkl'

def get_embeddings(model):
    V = model.wv.index2word
    embeddings = np.zeros((len(V), model.vector_size))

    for index, word in enumerate(V):
        embeddings[index, :] += model[word]
    return embeddings

def cluster_funs_by_kmeans(K):
    """
    興味で同じような興味は塊が多すぎて、同じような興味が出てくるのでそれを防ぐため、clusteringする
    current vocab_size => len(model.wv.vocab) 23402
    """
    model = load_model('fun2vec')
    embeddings = get_embeddings(model)
    clf = MiniBatchKMeans(n_clusters=K, batch_size=500, init_size=10000, random_state=0)
    clf.fit(embeddings)
    save(clf, FILE_KMEANS)
    # km = KMeans(n_clusters=1000
    # )

def check(words):
    clf = joblib.load(FILE_KMEANS)
    model = load_model('fun2vec')
    # for w in words:
    #     idx = result[model.wv.vocab[w].index]
    #     print(w, model.wv.index2word[idx])
    X = [model[word] for word in words]
    res = clf.predict(X)
    for w, center_id in zip(words, res):
        print(w, model.wv.index2word[center_id])

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
            if sim < 0.8:
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
        同一scoreの場合は単語の頻度が高いを優先する
        """
        if f1[1]['score'] == f2[1]['score']:
            print(f1[0], model.wv.vocab[f1[0]].count)
            print(f2[0], model.wv.vocab[f2[0]].count)
            return 1 if model.wv.vocab[f1[0]].count > model.wv.vocab[f2[0]].count else -1
        else:
            return 1 if f1[1]['score'] > f2[1]['score'] else -1

    cluster = sorted(cluster.items(), key=cmp_to_key(_compare), reverse=True)
    pprint(cluster)
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

    print(funs)
    return list(funs)

if __name__ == '__main__':
    # cluster_funs(1000)
    # check(['機械学習', 'プログラミング', 'エンジニア', 'サッカー', '野球', '英語'])
    from pprint import pprint
    model = load_model('word2vec')
    cluster_funs(model, ['ビール','焼酎','ワイン','シャンパン'])
    # cluster_funs(model, ['Perl','PHP','Ruby'])
    # cluster_funs(model, ['育児','芝居','宝塚','歌舞伎','映画','漫画','柴犬'])
    # cluster_funs(model, ['料理','競馬','歴史','野球','相撲'])
    # cluster_funs(model, ['指原莉乃','大島優子','高橋みなみ','前田敦子','小嶋陽菜','北原里英','柏木由紀','瀧野由美子'])
    # cluster_funs(model, ['スポーツ観戦', 'お笑い', 'フットサル', '映画', 'プログラミング', 'エンジニア', 'サッカー', '英語'])
    # cluster_funs(model, [ 'アイドル','２次元','ゲーム','アニメ','音楽'])
