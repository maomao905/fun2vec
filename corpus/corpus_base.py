import os
from util import read_sql, load_config
from word import Word
import re
from fun2vec import load_model
import gzip
import logging
import pandas as pd
from flask_script import Manager
from cluster import cluster_funs
from db import create_session, User, bulk_save
try:
    import cPickle as pickle
except ImportError:
    import pickle

config = load_config('file')
logging.config.dictConfig(load_config('log'))
_logger = logging.getLogger(__name__)

class BaseCorpus:
    __REGEX_URL = re.compile(r'((?:https?|ftp):\/\/[a-z\d\.\-\/\?\(\)\'\*_=%#@"<>!;]+)', re.IGNORECASE)

    def __init__(self):
        super().__init__()
        self._word = Word()
        logging.config.dictConfig(load_config('log'))
        self._logger = logging.getLogger(__name__)

    def extract(self):
        raise NotImplementedError()

    @classmethod
    def _replace_url(cls, text):
        """
        replace url with <URL>
        """
        urls = cls.__REGEX_URL.findall(text)
        for url in urls:
            text = text.replace(url, '<URL>')

        return text

    @staticmethod
    def get_corpus(file_name):
        corpus = []
        if os.path.exists(file_name):
            with gzip.open(file_name, 'rb') as f:
                corpus = pickle.load(f)
        return corpus

manager = Manager(usage='Perform corpus operations')
@manager.command
def create_word2vec_corpus():
    corpus = Word2vecCorpus()
    corpus.extract()

@manager.command
def create_fun2vec_corpus():
    from corpus.corpus_fun2vec import Fun2vecCorpus
    session = create_session()
    corpus = Fun2vecCorpus()
    _logger.info('Running query...')
    users_with_funs = []

    try:
        for idx, user in enumerate(session.query(User).filter(User.verified==0).yield_per(500), 1):
            funs = corpus.extract(user.description)
            # 興味が２つ以上の場合だけ
            if len(funs) >= 2:
                user.funs = '/'.join(funs)
                users_with_funs.append(user)

            if idx % 10000 == 0:
                bulk_save(session, users_with_funs)
                users_with_funs = []
                _logger.info(f'Finished {idx} profiles')

        bulk_save(session, users_with_funs)
    except Exception as e:
        session.rollback()
        _logger.error(e)
    finally:
        session.close()

@manager.command
def write_fun2vec_corpus_to_file():
    # most_similarでextendせずにcorpusを作る
    with gzip.open(config['fun2vec']['corpus'], 'wb') as f:
        pickle.dump(user_funs, f)
    logger.info('Saved corpus of {} profiles in {}'.format(len(user_funs), config['fun2vec']['corpus']))

@manager.command
def create_clustered_fun2vec_corpus():
    """
    既存のfun2vec corpusから似た興味をグループ化して、新たなcorpusを作る
    """
    with gzip.open(config['fun2vec']['corpus'], 'rb') as f:
        corpus = pickle.load(f)
    model = load_model('word2vec')
    clustered_corpus = []
    for i, user_funs in enumerate(corpus, 1):
        funs = cluster_funs(model, user_funs)
        if len(funs) >= 2:
            clustered_corpus.append(funs)
        if i % 10000 == 0:
            logger.info('Finished {} profiles'.format(i))
    with gzip.open(config['fun2vec_clustered']['corpus'], 'wb') as f:
        pickle.dump(clustered_corpus, f)
        logger.info('Saved corpus of {} profiles in {}'.format(len(clustered_corpus), config['fun2vec_clustered']['corpus']))

@manager.option('-m', '--model_name', dest='model_name')
@manager.option('-n', '--topn', dest='topn', default=100)
def check_corpus(model_name, topn):
    """
    corpusチェック
    randomにtopn件のprofile(単語リスト)取得
    """
    import random

    with gzip.open(config[model_name]['corpus'], 'rb') as f:
        corpus = pickle.load(f)
    for profile in random.sample(corpus, topn):
        print('-' * 50)
        print(profile)

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
