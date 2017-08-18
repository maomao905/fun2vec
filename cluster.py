from sklearn.cluster import MiniBatchKMeans
from word2vec import load_model
from sklearn.externals import joblib
import numpy as np

FILE_FUN2VEC = 'data/fun.model'
FILE_KMEANS = 'data/kmeans_fun.pkl'

def get_embeddings(model):
    V = model.wv.index2word
    embeddings = np.zeros((len(V), model.vector_size))

    for index, word in enumerate(V):
        embeddings[index, :] += model[word]
    return embeddings

def cluster_funs(K):
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

if __name__ == '__main__':
    # cluster_funs(5000)
    check(['機械学習', 'プログラミング', 'エンジニア', 'サッカー', '野球', '英語'])
