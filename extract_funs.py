from model import create_session, User
from sqlalchemy.sql.expression import text
from util import read_sql
from wakati import extract_words
import re
from itertools import combinations
import fun2vec
import random
import pickle
import logging

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s][%(levelname)-5s][%(name)-10s][%(funcName)-10s] %(message)s')
logger = logging.getLogger(__name__)

FILE_SQL = 'sql/filter_interests.sql'
FILE_DICTIONARY = 'data/dictionary.pkl'
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
    model = fun2vec.load_model()
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
    model = fun2vec.load_model()
    dictionary = set()
    for funs in user_funs:
        # 興味３つの組み合わせを取得
        combs = list(combinations(funs, 3))
        random.shuffle(combs)
        # 組み合わせの数が多すぎるので、興味の数だけ拡張を行う
        combs = combs[:len(funs)]
        # 既存の興味をまずに辞書登録
        dictionary.update(funs)
        for idx, comb in enumerate(combs):
            try:
                # ３つの興味ベクトルを足して、それに近い興味も取得
                near_funs = set(w[0] for w in model.most_similar(positive=list(comb)))
                dictionary.update(near_funs)
            except KeyError:
                # 対象の興味が存在しなかった場合はスキップ
                continue
    return list(dictionary)

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

    return list(set(fun_words))

def create_dictionary():
    user_funs = get_best_profile()
    logger.info('Extending funs to create dictionary...')
    dictionary = extend_funs(user_funs)
    with open(FILE_DICTIONARY, 'wb') as f:
        pickle.dump(dictionary, f)
    logger.info('Saved dictionary of {} words in {}'.format(len(dictionary), FILE_DICTIONARY))

if __name__ == '__main__':
    create_dictionary()