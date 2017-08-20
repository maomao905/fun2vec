from model import create_session, User
from sqlalchemy.sql.expression import text
from util import read_sql, load_config
from morph import extract_words
import re
from itertools import combinations
from collections import defaultdict, Counter
from fun2vec import load_model
import random
import pickle
import logging
from pprint import pprint
import pandas as pd
import numpy as np
from flask_script import Manager

logging.config.dictConfig(load_config('log'))
logger = logging.getLogger(__name__)

config = load_config('file')
FILE_SQL = 'sql/filter_interests.sql'
FILE_TOTAL_FUNS = 'data/total_funs_v3.csv'
MAX_WORD_LENGTH = 10
REGEX_FUNS = re.compile(r'([ぁ-んァ-ヶー一-龠]{1,%d}(?P<sep>、|,|/|\s|#|・)){2}' % MAX_WORD_LENGTH)
REGEX_URL = re.compile(r'((?:https?|ftp):\/\/[a-z\d\.\-\/\?\(\)\'\*_=%#@"<>!;]+)', re.IGNORECASE)
REGEX_INVALID = re.compile(r'公式|宣伝|bot|ボット', re.IGNORECASE)

def _get_best_profile():
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
        funs = _find_fun_part(profile[0])
        # 興味が２つ以上の場合だけ
        if len(funs) >= 2:
            user_funs.append(funs)

    return user_funs

def extend_funs(user_funs):
    """
    ユーザーの興味データを拡張し、辞書を作る
    """
    # Twitterプロフィール情報から作成したword2vecモデル
    model = load_model('word2vec')
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
                near_funs = set(w for w, sim in model.most_similar(positive=list(comb), topn=3) if sim > 0.8)
                # 辞書に登録
                list(map(lambda f: fun2id[f], near_funs))
            except KeyError:
                # 対象の興味が存在しなかった場合はスキップ
                continue
    return fun2id

def _replace_url(text):
    """
    urlを<URL>に置き換え
    """
    urls = REGEX_URL.findall(text)
    for url in urls:
        text = text.replace(url, '<URL>')

    return text

def _invalid_profile(text):
    return bool(REGEX_INVALID.search(text))

def _find_fun_part(text):
    """
    正規表現で「三浦半島探検/ヒリゾ/伊豆が好きです。」の部分だけを取得
    形態素解析で興味を抽出
    """
    fun_words = []
    # 公式アカウント・Botなどは除外
    if _invalid_profile(text):
        return []

    ma = REGEX_FUNS.search(text)
    if ma is None:
        return []

    # funs: ['三浦半島探検', 'ヒリゾ', '伊豆が好きです。']
    funs = text[ma.start():].split(ma.group('sep'))

    for idx, fun in enumerate(funs, 1):
        words = extract_words(fun)
        # 配列の最後のみ区切りがわからず全部解析するので「伊豆が好きです。」=> 伊豆, 好き => 伊豆のみ抽出
        # 英語の場合があるのでbyteでカウント
        if idx == len(funs) or len(fun.encode('utf-8')) > MAX_WORD_LENGTH * 3:
            if len(words) > 0:
                last_word = words[0]
                fun_words.extend([last_word])
                # 残りのtext
                try:
                    next_start_idx = text.index(last_word) + len(last_word)
                    next_text = text[next_start_idx:]
                    # 残りの文を再起的に見る
                    fun_words.extend(_find_fun_part(next_text))
                except ValueError:
                    # last_wordが原型と異なる場合は諦める
                    pass
            break
        else:
            fun_words.extend(words)

    return set(fun_words)

manager = Manager(usage='Perform corpus operations')
@manager.command
def create_word2vec_corpus():
    corpus = []
    session = create_session()
    logger.info('Fetching twitter profile data from DB...')
    res = session.query(User.description).filter(User.verified==0).all() # 公式アカウントは除く
    logger.info('Fetched {} twitter profiles'.format(len(res)))
    logger.info('Extracting words from twitter profiles...')
    STOP_WORDS = pd.read_csv(config['stop_words'], header=None).values.flatten().tolist()
    for idx, profile in enumerate(res, 1):
        profile = profile[0]
        if profile is None:
            continue
        words = extract_words(profile, STOP_WORDS)
        if len(words) >= 2:
            corpus.append(words)
        if idx % 10000 == 0:
            logger.info('Finished {} records'.format(idx))
    with open(config['word2vec']['corpus'], 'wb') as f:
        pickle.dump(corpus, f)
    logger.info('Saved corpus of {} sentences in {}'.format(len(corpus), config['word2vec']['corpus']))

@manager.command
def create_fun2vec_dictionary():
    user_funs = _get_best_profile()
    logger.info('Extending funs to create dictionary...')
    dictionary = dict(extend_funs(user_funs))
    with open(config['fun2vec']['dictionary'], 'wb') as f:
        pickle.dump(dictionary, f)
    logger.info('Saved dictionary of {} words in {}'.format(len(dictionary), config['fun2vec']['dictionary']))

@manager.command
def create_fun2vec_corpus():
    'use dictionary of extracted funs to create fun corpus from word corpus'
    # with open(config['fun2vec']['dictionary'], 'rb') as f:
    #     dictionary = pickle.load(f)
    #     dictionary_words = list(dictionary.keys())
    dictionary_words = pd.read_csv('data/total_funs_v3.csv', header=None).values.flatten().tolist()

    with open(config['word2vec']['corpus'], 'rb') as f:
        word2vec_corpus = pickle.load(f)

    logger.info('Creating fun2vec corpus...')
    fun2vec_corpus = []
    for idx, words in enumerate(word2vec_corpus, 1):
        funs = [word for word in words if word in dictionary_words]
        # 興味が２つ以上の場合のみ
        if len(funs) >= 2:
            fun2vec_corpus.append(funs)
        if idx % 10000 == 0:
            logger.info('Finished {} sentences'.format(idx))

    with open(config['fun2vec']['corpus'], 'wb') as f:
        pickle.dump(fun2vec_corpus, f)
    logger.info('Saved corpus of {} sentences in {}'.format(len(fun2vec_corpus), config['fun2vec']['corpus']))

def get_similar_words(model, positive, negative=[], cut_sim=0.8, topn=1):
    try:
        res = model.most_similar(positive=positive, negative=negative, topn=topn)
    except KeyError:
        return []
    return [w for w, sim in res if sim > cut_sim]

def _extend_vocab(model, words):
    """
    既存のvocabをmost_similarして重複しないものを新たに返す
    """
    comb_sim_words = set(get_similar_words(model, words, topn=5))
    sim_words1 = set(get_similar_words(model, words[0], topn=10))
    sim_words2 = set(get_similar_words(model, words[1], topn=10))
    return comb_sim_words - sim_words1 - sim_words2

@manager.command
def create_dictionary_from_samples():
    """
    choose good words by self-check => extend those words by gensim most_similar
    まとめるとあなたは〇〇が好き
    """
    df = pd.read_csv('data/sample_funs.csv', header=None, names=['fun'])
    # import pdb; pdb.set_trace()
    model = load_model('fun2vec')

    # corpus = [['議論', '英語', 'ビリヤード', 'サッカー', 'プログラミング', 'エンジニア', '機械学習', '耳かき', 'コミュ障', '幼い', 'ドライブ'],
    # ['カメラ', '機械学習', 'お笑い', 'スケート'], ['アニメ', 'オタク', '東京大学', '公務員'],
    # ['阪神','PC','鉄道','数学','統計学','音楽','教育','アニメ','仏教','台湾','語学学習'], ['無機化学','有機化学','生化学','薬理学','免疫学','統計学','物理数学'],
    # ['読書','生物学','統計学','ソフトテニス','ソフトボール'], ['猫','犬','柴犬','ディズニー','ミスチル','サッカー','フットサル']]
    logger.info('Extending vocabulary from sample dictionary...')
    # サンプルから２つ取得
    while True:
        sample_vocabs = df.sample(2).values.flatten().tolist()
        new_vocabs = _extend_vocab(model, sample_vocabs)
        if len(new_vocabs) > 0:
            new_vocabs = list(new_vocabs - set(df[df.fun.isin(new_vocabs)].values.flatten()))
            if len(new_vocabs) > 0:
                df_new = pd.DataFrame(np.array(new_vocabs).reshape(1, -1).T, columns=['fun'])
                df = df.append(df_new, ignore_index=True).drop_duplicates()
                if len(df) % 1000 == 0:
                    logger.info('Total {} vocabs'.format(len(df)))
                # 辞書2000語になったら終了した
                if len(df) >= 2000:
                    break

    # df.to_csv(FILE_TOTAL_FUNS, index=False, header=False)
    logger.info('Done! Saved {} vocabs in {}'.format(len(df), FILE_TOTAL_FUNS))

def get_middle_words(model, w1, w2):
    # w1 = matutils.unitvec(np.array([sim for w, sim in model.most_similar(w1, topn=10)]))
    # w2 = matutils.unitvec(np.array([sim for w, sim in model.most_similar(w2, topn=10)]))
    # weight1 = np.mean(matutils.unitvec(n)[sim**2 for w, sim in model.most_similar(w1, topn=10)])
    # import pdb; pdb.set_trace()
    # cosine distance
    try:
        cos_dist1 = 1 - np.mean([sim for w, sim in model.most_similar(w1, topn=10)])
        cos_dist2 = 1 - np.mean([sim for w, sim in model.most_similar(w2, topn=10)])
    except KeyError as e:
        print(e.args[0])
        return
    print(cos_dist1, cos_dist2)
    # indices = [model.wv.vocab['提案'].index for w in model.most_similar
    # sim_words = [w for w, sim in model.most_similar(w1, topn=10)]
    # sim_vec = np.array([model.wv.word_vec(word) for word in sim_words])
    # dist1 = np.linalg.norm(model.wv.word_vec(w1)-sim_vec)

    # use norm (computationally efficient)
    w1_vec = model.wv.word_vec(w1, use_norm=True)
    w2_vec = model.wv.word_vec(w2, use_norm=True)
    # import pdb; pdb.set_trace()
    # 重みづけした単語1ベクトル+単語2ベクトルの中間点
    middle = w1_vec - ((w1_vec - w2_vec) * (cos_dist1 / (cos_dist1 + cos_dist2)))
    # unitvec -> scale a vector to unit length(euclid距離で割る=l2-norm)
    # np.array([w1_vec, w2_vec]).mean(axis=0)
    # scale
    middle = matutils.unitvec(np.array(middle)).astype(REAL)
    res = model.similar_by_vector(middle, topn=20)
    # w1とw2は除く
    res = [(w, sim) for w, sim in res if w not in [w1, w2]]
    pprint(res)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.ERROR)
    from gensim import matutils
    from numpy import exp, log, dot, zeros, outer, random, dtype, float32 as REAL
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit import prompt
    import argparse
    parser = argparse.ArgumentParser(description='Show similar words/funs')
    history = InMemoryHistory()
    model = load_model('fun2vec')
    try:
        while True:
            text = prompt('words> ', history=history)
            if not text:
                continue
            words = text.split()
            if len(words) != 2:
                print('Please specify two words')
                continue
            get_middle_words(model, words[0], words[1])
    except (EOFError, KeyboardInterrupt):
        print('\nExit.')
