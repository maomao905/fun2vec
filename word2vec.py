import os, sys
import pickle
from gensim.models import word2vec
from wakati import create_wakati
from flask_script import Manager
import logging
from pprint import pprint
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit import prompt
import argparse
from collections import OrderedDict

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s][%(levelname)-5s][%(name)-10s][%(funcName)-10s] %(message)s')
logger = logging.getLogger(__name__)

FILE_WORD2VEC = 'data/profile.model'
FILE_FUN2VEC = 'data/fun.model'
FILE_WAKATI = 'data/wakati.txt'

manager = Manager(usage='Create word2vec/fun2vec model')
@manager.command
def create_word2vec():
    'Extract words -> Create wakati sentences -> Create word2vec model'
    create_wakati()
    sentences = word2vec.Text8Corpus(FILE_WAKATI)
    logger.info('Creating word2vec model...')
    model = word2vec.Word2Vec(sentences, size=200, min_count=10, window=5)
    model.save(FILE_WORD2VEC)
    logger.info('Saved model in {}'.format(FILE_WORD2VEC))

@manager.command
def create_fun2vec():
    'Create fun2vec model'
    FILE_CORPUS = 'data/corpus.pkl'
    FILE_DICTIONARY = 'data/dictionary.pkl'
    with open(FILE_CORPUS, 'rb') as f:
        corpus = pickle.load(f)
    with open(FILE_DICTIONARY, 'rb') as f:
        dictionary = pickle.load(f)
        reverse_dictionary = {v: k for k, v in dictionary.items()}
        del dictionary

    sentences = []
    for fun_ids in corpus:
        funs = []
        for fun_id in fun_ids:
            funs.append(reverse_dictionary[fun_id])
        sentences.append(funs)
    # defaultでcbowらしい
    model = word2vec.Word2Vec(sentences, size=200, min_count=30, window=20)
    model.save(FILE_FUN2VEC)
    logger.info('Saved model in {}'.format(FILE_FUN2VEC))

@manager.option('-m', '--model', dest='model_name', default='fun2vec')
@manager.option('-n', '--topn', dest='topn', default=300)
@manager.option('-w', '--target_word', dest='target_word', default=None)
def check_vocab(model_name, topn, target_word):
    'Check model vocabrary in frequent order'
    logging.getLogger().setLevel(logging.ERROR)
    model = load_model(model_name)
    if target_word:
        print(model.wv.vocab[target_word].count, target_word)
    else:
        for idx, word in enumerate(model.wv.index2word):
            print(model.wv.vocab[word].count, word)
            if idx >= int(topn):
                break

def load_model(model_name):
    if model_name == 'word2vec':
        return word2vec.Word2Vec.load(FILE_WORD2VEC)
    if model_name == 'fun2vec':
        return word2vec.Word2Vec.load(FILE_FUN2VEC)

def main(args):
    model_name = args.model
    topn = int(args.topn)
    restrict_vocab = int(args.restrict_vocab) if args.restrict_vocab else None

    logging.getLogger().setLevel(logging.ERROR)
    models = OrderedDict()
    if model_name in ['word2vec', 'all']:
        models['word2vec'] = load_model('word2vec')
    if model_name in ['fun2vec', 'all']:
        models['fun2vec'] = load_model('fun2vec')
    history = InMemoryHistory()
    try:
        while True:
            text = prompt('words> ', history=history)
            if not text:
                continue
            for name, model in models.items():
                print('--------------', name, '--------------')
                try:
                    pprint(model.most_similar(positive=text.split(), topn=topn, restrict_vocab=restrict_vocab))
                except KeyError as e:
                    print(e.args[0])
                    continue
    except (EOFError, KeyboardInterrupt):
        print('\nExit.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Show similar words/funs')
    parser.add_argument('-m', '--model', default='all', help='specify which model to use')
    parser.add_argument('-n', '--topn', default=10, help='specify the number of output')
    parser.add_argument('-rv', '--restrict_vocab', default=None, help='specify how the number of word vectors you will check in the vocabulary order')
    args = parser.parse_args()
    main(args)
