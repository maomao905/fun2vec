from corpus.corpus_base import BaseCorpus
from db import create_session, User, bulk_save
import re
from util import load_config, _pickle, _unpickle
from flask_script import Manager
import logging
from random import shuffle
from model import Model
from cluster import cluster_funs

logging.config.dictConfig(load_config('log'))
_logger = logging.getLogger(__name__)
config = load_config('file')

class Fun2vecCorpus(BaseCorpus):
    __MAX_WORD_LENGTH = 12
    __REGEX_CHAR = '[1-9a-zぁ-んァ-ヶー一-龠()（）!！-]{1,%d}' % __MAX_WORD_LENGTH
    __REGEX_FUN_PREV = re.compile(r'(?P<fun>{char}?)((する)?こと)?(に(興味|はまって)|(を|の?が)趣味|を(こよなく)?愛する|が?(?:大?好き|大好物|だいすき))'.format(char=__REGEX_CHAR))
    __REGEX_HOBBY_FOLLOW = re.compile(r'趣味(は|で^す|：|:|→|⇒|\=)\s?(?P<fun>{char})'.format(char=__REGEX_CHAR))
    __REGEX_SEP_FUNS = re.compile(r'({char}(?P<sep>とか|やら|、|,\s?|，|\s?/\s?|#|・|\s?／\s?|//|\|)(?:{char}(?P=sep))+{char})' \
        .format(char=__REGEX_CHAR), re.IGNORECASE)
    # REGEX_INTEREST_FOLLOW = re.compile(r'興味(は|：|:|→|⇒|\=|が?(有|あ)る(事|こと|も?の)は)\s?(?P<fun>{char})'.format(char=__REGEX_CHAR))
    __REGEX_AND_FUN = re.compile(r'((%s(?P<sep>とか?)){3,}%s)' % (__REGEX_CHAR, __REGEX_CHAR))

    def __init__(self):
        super().__init__()

    def extract(self, text):
        """
        下記のような区切りがあるを興味・関心とみなし取得する。
        ex) 最近は、三浦半島探検/ヒリゾ/伊豆/箱根/道志/長野上田/ドライブ/秘湯が好きです。
        return: [['三浦半島探検','ヒリゾ', '伊豆'], ['音楽', '落語', '旅']]
        """
        funs = []
        text = self._replace_url(text)
        funs.extend(self.__find_fun_words(text))
        funs.extend(self.__find_separated_fun_words(text))
        return funs

    def __find_separated_fun_words(self, text):
        """
        正規表現で「三浦半島探検/ヒリゾ/伊豆が好きです。」の部分だけを取得
        形態素解析で興味を抽出
        return: ['三浦半島探検','ヒリゾ','伊豆']
        """
        fun_words = []

        ma = self.__REGEX_SEP_FUNS.search(text)
        if ma is None:
            return []

        # funs: ['三浦半島探検', 'ヒリゾ', '伊豆が好きです。']
        funs = ma.group().split(ma.group('sep'))
        for idx, fun in enumerate(funs):
            words = self._word.preprocess(fun)
            if len(words) > 0:
                if idx == 0:
                    # 区切られた最初の文はどこから最初かわからないので、一番最後だけ取得
                    first_word = words[-1]
                    fun_words.extend([first_word])
                elif idx + 1 == len(funs):
                    # 区切られた最後の文はどこまでかわからないので、一番先頭だけ取得
                    # 「伊豆が好きです。」=> 伊豆, 好き => 伊豆のみ抽出
                    last_word = words[0]
                    fun_words.extend([last_word])
                    try:
                        # 残りのtext
                        next_start_idx = text.index(fun) + fun.index(last_word) + len(last_word)
                        next_text = text[next_start_idx:]
                    except ValueError:
                        # last_wordが原型と異なる場合
                        next_text = text[ma.end():]
                    # 残りの文を再起的に見る
                    fun_words.extend(self.__find_separated_fun_words(next_text))
                else:
                    fun_words.extend(words)
            else:
                # 区切られた最後の文で何も取得できなかったとき
                if idx + 1 == len(funs):
                    next_text = text[ma.end():]
                    fun_words.extend(self.__find_separated_fun_words(next_text))

        return fun_words


    def __find_fun_words(self, text):
        fun_words = []
        for _regex in [self.__REGEX_FUN_PREV, self.__REGEX_HOBBY_FOLLOW]:
            matches = [res.group('fun') for res in _regex.finditer(text)]
            for __ma in matches:
                words = self._word.preprocess(__ma)
                if len(words) > 0:
                    fun_words.extend(words)

        ma = self.__REGEX_AND_FUN.search(text)
        if ma and 'とか' not in text:
            for __ma in ma.group().split('と'):
                words = self._word.preprocess(__ma)
                if len(words) > 0:
                    fun_words.extend(words)

        return fun_words

manager = Manager(usage='Perform fun2vec corpus operations')
@manager.command
def create():
    corpus = []
    session = create_session()
    fc = Fun2vecCorpus()
    try:
        for idx, user in enumerate(session.query(User).filter(User.verified==0).yield_per(500), 1):
            funs = list(set(fc.extract(user.description)))
            if len(funs) > 0:
                shuffle(funs)
                corpus.append(funs)
            if idx % 10000 == 0:
                _logger.info(f'{idx} profiles')
    except Exception as e:
        _logger.error(e)
    finally:
        session.close()
    _pickle(corpus, config['corpus']['fun2vec'])
    _logger.info(f"Saved corpus of {len(corpus)} sentences in {config['corpus']['fun2vec']}")

@manager.command
def cluster():
    """
    既存のfun2vec corpusから似た興味をグループ化して、新たなcorpusを作る
    """
    clustered_corpus = []
    corpus = _unpickle(config['corpus']['fun2vec'])
    word2vec_model = Model.load_model('word2vec')
    for i, user_funs in enumerate(corpus, 1):
        funs = cluster_funs(word2vec_model, user_funs)
        if len(funs) >= 2:
            clustered_corpus.append(funs)
        if i % 10000 == 0:
            _logger.info(f'Finished {i} profiles')
    _pickle(clustered_corpus, config['corpus']['fun2vec_clustered'])
    _logger.info(f"Saved corpus of {len(clustered_corpus)} profiles in {config['corpus']['fun2vec_clustered']}")

@manager.command
def cluster_by_kmeans():
    """
    Use KMeans to group similar words.
    """
    import os, sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
    from cluster import Cluster
    from collections import defaultdict
    import random

    clustered_corpus = []
    corpus = _unpickle(config['corpus']['fun2vec'])
    clf = Cluster(config['cluster']['kmeans'])
    m = Model('word2vec')
    cluster = dict(zip(m.vocab, clf.predict(m.vector)))
    del m, clf # memory friendly

    for i, words in enumerate(corpus, 1):
        centroids = defaultdict(list)
        for word in words:
            label = cluster.get(word)
            centroids[label].append(word)
        # if there are the words which have the same labels, randomly choose one of them and remove others.
        clustered_words = [random.choice(v) if k is not None and len(v) >= 2 else v[0] for k, v in centroids.items()]

        if len(clustered_words) >= 2:
            clustered_corpus.append(clustered_words)
            if i < 100:
                print('----------------------------')
                print(words)
                print(clustered_words)

        if i % 10000 == 0:
            _logger.info(f'Finished {i} profiles')
    _pickle(clustered_corpus, config['corpus']['fun2vec_clustered'])
    _logger.info(f"Saved corpus of {len(clustered_corpus)} profiles in {config['corpus']['fun2vec_clustered']}")
