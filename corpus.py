from model import create_session, User
from sqlalchemy.sql.expression import text
from util import read_sql
from wakati import extract_words
import re
from itertools import combinations
from collections import defaultdict, Counter
import word2vec
import random
import pickle
import logging
from pprint import pprint
import pandas as pd
import numpy as np

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s][%(levelname)-5s][%(name)-10s][%(funcName)-10s] %(message)s')
logger = logging.getLogger(__name__)

FILE_SQL = 'sql/filter_interests.sql'
FILE_DICTIONARY = 'data/dictionary.pkl'
FILE_WAKATI = 'data/wakati.txt'
FILE_CORPUS = 'data/corpus.pkl'
FILE_TOTAL_FUNS = 'data/total_funs_v2.csv'
MAX_WORD_LENGTH = 10
REGEX_FUNS = re.compile(r'([ぁ-んァ-ヶー一-龠]{1,%d}(?P<sep>、|,|/|\s|#|・)){2}' % MAX_WORD_LENGTH)

def get_best_profile():
    """
    下記のような区切りがあるを興味・関心とみなし取得する。
    ex) 最近は、三浦半島探検/ヒリゾ/伊豆/箱根/道志/長野上田/ドライブ/秘湯が好きです。
    return: [['三浦半島探検','ヒリゾ', '伊豆'], ['音楽', '落語', '旅']]
    """
    session = create_session()
    sql = read_sql(FILE_SQL)
    logger.info('Running query...\n{}'.format(sql))
    res = session.query(User.description).from_statement(text(sql)).all()
    logger.info('Analyze {} profiles'.format(len(res)))
    user_funs = []
    for profile in res:
        # funs: ['三浦半島探検','ヒリゾ','伊豆']
        funs = find_fun_part(profile[0])
        # 興味が３つ以上の場合だけ
        if len(funs) >= 3:
            user_funs.append(funs)

    return user_funs

def extend_funs(user_funs):
    """
    ユーザーの興味データを拡張し、辞書を作る
    """
    # Twitterプロフィール情報から作成したword2vecモデル
    model = word2vec.load_model('word2vec')
    # 興味辞書
    fun2id = defaultdict(lambda: len(fun2id))
    for funs in user_funs:
        # 興味３つの組み合わせを取得
        combs = list(combinations(list(funs), 3))
        random.shuffle(combs)
        # 組み合わせの数が多すぎるので、興味の数だけ拡張を行う
        combs = combs[:len(funs)]
        # 既存の興味をまず辞書に登録
        list(map(lambda f: fun2id[f], funs))
        for idx, comb in enumerate(combs):
            try:
                # ３つの興味ベクトルを足して、それに近い興味も取得
                near_funs = set(w[0] for w in model.most_similar(positive=list(comb), topn=3))
                # 辞書に登録
                list(map(lambda f: fun2id[f], near_funs))
            except KeyError:
                # 対象の興味が存在しなかった場合はスキップ
                continue
    return fun2id

def find_fun_part(text):
    """
    正規表現で「三浦半島探検/ヒリゾ/伊豆が好きです。」の部分だけを取得
    形態素解析で興味を抽出
    """
    fun_words = []
    ma = REGEX_FUNS.search(text)
    try:
        # funs: ['三浦半島探検', 'ヒリゾ', '伊豆が好きです。']
        funs = text[ma.start():].split(ma.group('sep'))
    except AttributeError:
        return fun_words
    for idx, fun in enumerate(funs):
        words = extract_words(fun)
        # 配列の最後のみ区切りがわからず全部解析するので「伊豆が好きです。」=> 伊豆, 好き => 伊豆のみ抽出
        # 英語の場合があるのでbyteでカウント
        if idx + 1 == len(funs) or len(fun.encode('utf-8')) > MAX_WORD_LENGTH * 3:
            if words:
                fun_words.extend([words[0]])
            break
        else:
            fun_words.extend(words)

    return set(fun_words)

def create_dictionary():
    user_funs = get_best_profile()
    logger.info('Extending funs to create dictionary...')
    dictionary = dict(extend_funs(user_funs))
    with open(FILE_DICTIONARY, 'wb') as f:
        pickle.dump(dictionary, f)
    logger.info('Saved dictionary of {} words in {}'.format(len(dictionary), FILE_DICTIONARY))

def create_corpus():
    corpus = []
    with open(FILE_DICTIONARY, 'rb') as f:
        dictionary = pickle.load(f)

    with open(FILE_WAKATI, 'r') as f:
        wakati = f.readline()
        while wakati:
            wakati = f.readline()
            corpus.append([word for word in set(wakati.strip().split(' ')) if word in dictionary])

    with open(FILE_CORPUS, 'wb') as f:
        pickle.dump(corpus, f)
    logger.info('Saved corpus of {} sentences in {}'.format(len(corpus), FILE_CORPUS))

def get_similar_words(model, positive, negative=[], cut_sim=0.8, topn=1):
    res = model.most_similar(positive=positive, negative=negative, topn=topn)
    sim_words = [w for w, sim in res if sim > cut_sim]
    return sim_words

def get_best_corpus():
    """
    choose good words by self-check => extend those words by gensim most_similar
    まとめるとあなたは〇〇が好き
    """
    with open(FILE_CORPUS, 'rb') as f:
        corpus = pickle.load(f)

    df = pd.read_csv('data/best_funs.csv', header=None, names=['fun'])
    # import pdb; pdb.set_trace()
    model = word2vec.load_model('fun2vec')

    # corpus = [['議論', '英語', 'ビリヤード', 'サッカー', 'プログラミング', 'エンジニア', '機械学習', '耳かき', 'コミュ障', '幼い', 'ドライブ'],
    # ['カメラ', '機械学習', 'お笑い', 'スケート'], ['アニメ', 'オタク', '東京大学', '公務員'],
    # ['阪神','PC','鉄道','数学','統計学','音楽','教育','アニメ','仏教','台湾','語学学習'], ['無機化学','有機化学','生化学','薬理学','免疫学','統計学','物理数学'],
    # ['読書','生物学','統計学','ソフトテニス','ソフトボール'], ['猫','犬','柴犬','ディズニー','ミスチル','サッカー','フットサル']]
    logger.info('Adding new funs from labeled funs...')
    for idx, words in enumerate(corpus):
        # そのプロフィールに存在する正解興味
        best_funs = df[df.fun.isin(words)].values.flatten().tolist()
        # 2つ以上正解興味に存在していたら
        if len(best_funs) >= 2:
            # 正解興味に一番近いワードを取得
            words = get_similar_words(model, positive=best_funs, topn=1)
            # もし近い興味が類似度0.8以上で存在したら
            if len(words) > 0:
                # 新たな興味と既存の興味を引き算したものを再度most_similar
                words2 = get_similar_words(model, positive=best_funs, negative=words, topn=3)
                df_new = pd.DataFrame(np.array(words+words2).reshape(1, -1).T, columns=['fun'])
                print(best_funs, words+words2)
                df = df.append(df_new, ignore_index=True).drop_duplicates()
            # combs = list(combinations(list(words), 2))
            # random.shuffle(combs)
            # 組み合わせの数が多すぎるので、興味の数だけ拡張を行う
            # combs = combs[:len(words)]
            # sim_words = []
            # comb_count = 0
            # for comb in combs:
            #     try:
            #         # cos類似度0.8以上の単語を追加
            #         sim_words.extend([w for w, sim in model.most_similar(comb, topn=3)])
            #         comb_count += 1
            #     except KeyError:
            #         continue
            # counter = Counter(sim_words)
            # print('comb_count', comb_count)
            # print('sim_words', counter)
        if (idx + 1) % 10000 == 0:
            break
            logger.info('Finished {} sentences'.format(idx+1))
    df.to_csv(FILE_TOTAL_FUNS, index=False, header=False)
    logger.info('Done! Saved total funs in {}'.format(FILE_TOTAL_FUNS))

def get_middle_words(model, w1, w2):
    # w1 = matutils.unitvec(np.array([sim for w, sim in model.most_similar(w1, topn=10)]))
    # w2 = matutils.unitvec(np.array([sim for w, sim in model.most_similar(w2, topn=10)]))
    # weight1 = np.mean(matutils.unitvec(n)[sim**2 for w, sim in model.most_similar(w1, topn=10)])
    weight1 = np.sum([sim for w, sim in model.most_similar(w1, topn=10)])
    weight2 = np.sum([sim for w, sim in model.most_similar(w2, topn=10)])
    print('------------------')
    print(weight1, weight2)
    # use norm (computationally efficient)
    w1_vec = model.wv.word_vec(w1, use_norm=True)
    w2_vec = model.wv.word_vec(w2, use_norm=True)
    # import pdb; pdb.set_trace()
    middle = w1_vec - ((w1_vec - w2_vec) * (weight2 / (weight1 + weight2)))
    # unitvec -> scale a vector to unit length(euclid距離で割る=l2-norm)
    # np.array([w1_vec, w2_vec]).mean(axis=0)
    mean = matutils.unitvec(np.array(middle)).astype(REAL) # 重みづけした単語1と単語2の平均vector
    res = model.similar_by_vector(mean, topn=20)
    pprint(res)

if __name__ == '__main__':
    # create_dictionary()
    # get_best_corpus()
    import sys
    from gensim import matutils
    from numpy import exp, log, dot, zeros, outer, random, dtype, float32 as REAL
    model = word2vec.load_model('fun2vec')
    args = sys.argv[1:]
    get_middle_words(model, args[0], args[1])
