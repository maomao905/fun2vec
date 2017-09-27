import os, sys
sys.path.append(os.getcwd())
from cluster import cluster_funs
from fun2vec import load_model
from pprint import pprint
from util import load_config
import random
import gzip, pickle
import logging
logging.config.dictConfig(load_config('log'))
logger = logging.getLogger(__name__)

config = load_config('file')

def test_cluster_funs():
    TEST_FUNS = [
        ['ビール','焼酎','ワイン','シャンパン'],
        ['Perl','PHP','Ruby'],
        ['育児','芝居','宝塚','歌舞伎','映画','漫画','柴犬', '犬'],
        ['料理','競馬','歴史','野球','相撲'],
        ['指原莉乃','大島優子','高橋みなみ','前田敦子','小嶋陽菜','北原里英','柏木由紀','瀧野由美子'],
        ['スポーツ観戦', 'お笑い', 'フットサル', '映画', 'プログラミング', 'エンジニア', 'サッカー', '英語'],
        ['アイドル','２次元','ゲーム','アニメ','音楽']
    ]
    model = load_model('word2vec')
    for funs in TEST_FUNS:
        print('-' * 70)
        print(funs)
        result = cluster_funs(model, funs)
        print('CLUSTERED FUNS:', result)
        print('DIFF--: ', (set(funs) - set(result)) or None)
        print('DIFF++: ', (set(result) - set(funs)) or None)

def test_cluster_funs_with_corpus(topn):
    """
    実際のcorpusの中身をclusteringするテスト
    """
    model = load_model('word2vec')
    with gzip.open(config['fun2vec']['corpus'], 'rb') as f:
        corpus = pickle.load(f)

    for profile in random.sample(corpus, topn):
        print('-' * 70)
        result = cluster_funs(model, profile)
        print('Original  FUNS:', profile)
        print('Clustered FUNS:', result)
        print('DIFF--: ', (set(profile) - set(result)) or None)
        print('DIFF++: ', (set(result) - set(profile)) or None)

if __name__ == '__main__':
    test_cluster_funs_with_corpus(30)
    # test_cluster_funs()
