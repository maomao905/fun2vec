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
try:
    import cPickle as pickle
except ImportError:
    import pickle

config = load_config('file')

class BaseaCorpus:
    __MAX_WORD_LENGTH = 12
    __REGEX_CHAR = '[a-zぁ-んァ-ヶー一-龠()（）!！-]{1,%d}' % MAX_WORD_LENGTH
    __REGEX_URL = re.compile(r'((?:https?|ftp):\/\/[a-z\d\.\-\/\?\(\)\'\*_=%#@"<>!;]+)', re.IGNORECASE)

    def __init__(self):
        super().__init__()
        self.__word = Word()
        logging.config.dictConfig(load_config('log'))
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _replace_url(text):
        """
        urlを<URL>に置き換え
        """
        urls = REGEX_URL.findall(text)
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
    # ALTER TABLE users DROP COLUMN word2vec_corpus_id;
    # ALTER TABLE users DROP COLUMN fun2vec_corpus_id;
    w_corpus = Word2vecCorpus()
    w_corpus.extract()

@manager.command
def create_fun2vec_dictionary():
    user_funs = _get_best_profile()
    logger.info('Extending funs to create dictionary...')
    dictionary = dict(extend_funs(user_funs))

    # with gzip.open(config['fun2vec']['dictionary'], 'wb') as f:
    #     pickle.dump(dictionary, f)
    logger.info('Saved dictionary of {} words in {}'.format(len(dictionary), config['fun2vec']['dictionary']))

@manager.command
def create_simple_fun2vec_corpus():
    # most_similarでextendせずにcorpusを作る
    user_funs = _extract_funs()

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
