#word2vecを学習させる

#必要なライブラリをインポート
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import numpy as np

#取り出す単語の範囲を指定
skip=0
limit=241#よく出る241単語のみをプロットする

X = model[model.wv.vocab]

tsne = TSNE(n_components=2, random_state=0)
tsne.fit_transform(X)
# np.set_printoptions(suppress=True)

#matplotlibでt-SNEの図を描く
plt.figure(figsize=(40,40))#図のサイズ
plt.scatter(tsne.embedding_[skip:limit, 0], tsne.embedding_[skip:limit, 1])

count = 0
for label, x, y in zip(vocab, tsne.embedding_[:, 0], tsne.embedding_[:, 1]):

    count +=1
    if(count<skip):continue
    plt.annotate(label, xy=(x, y), xytext=(0, 0), textcoords='offset points')
    if(count==limit):break
plt.show()
