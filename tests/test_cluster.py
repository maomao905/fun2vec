import unittest
from cluster import cluster_funs
from fun2vec import load_model
from pprint import pprint
from util import load_config
import logging
logging.config.dictConfig(load_config('log'))
logging.getLogger().setLevel(logging.CRITICAL)

class TestCluster(unittest.TestCase):

    def test_cluster_funs(self):
        TEST_FUNS = [
            ['ビール','焼酎','ワイン','シャンパン'],
            ['Perl','PHP','Ruby'],
            ['育児','芝居','宝塚','歌舞伎','映画','漫画','柴犬'],
            ['料理','競馬','歴史','野球','相撲'],
            ['指原莉乃','大島優子','高橋みなみ','前田敦子','小嶋陽菜','北原里英','柏木由紀','瀧野由美子'],
            ['スポーツ観戦', 'お笑い', 'フットサル', '映画', 'プログラミング', 'エンジニア', 'サッカー', '英語'],
            [ 'アイドル','２次元','ゲーム','アニメ','音楽']
        ]
        model = load_model('word2vec')
        for funs in TEST_FUNS:
            print('---------------------------')
            print(funs)
            result = cluster_funs(model, funs)
            print('CLUSTERED FUNS:', result)
            print('DIFF--: ', (set(funs) - set(result)) or None)
            print('DIFF++: ', (set(result) - set(funs)) or None)
