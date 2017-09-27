import os, sys
try:
    import cPickle as pickle
except ImportError:
    import pickle
import gzip
from gensim.models import word2vec
from flask_script import Manager
import logging
from pprint import pprint
from collections import OrderedDict
from util import load_config

logging.config.dictConfig(load_config('log'))
logger = logging.getLogger(__name__)

config = load_config('file')

manager = Manager(usage='Create word2vec/fun2vec model')
@manager.command
def create_word2vec():
    'Create word2vec model'
    with gzip.open(config['word2vec']['corpus'], 'rb') as f:
        sentences = pickle.load(f)
    logger.info('Creating word2vec model from {} sentences...'.format(len(sentences)))
    model = word2vec.Word2Vec(sentences, size=700, min_count=30, window=5, compute_loss=True)
    model.init_sims(replace=True) # to trim unneeded model memory by L2-norm
    logger.info('Loss is {}'.format(model.get_latest_training_loss()))
    save_model(model, config['word2vec']['model'])

@manager.command
def create_fun2vec():
    'Create fun2vec model'
    with gzip.open(config['fun2vec']['corpus'], 'rb') as f:
        funs = pickle.load(f)
    logger.info('Creating fun2vec model from {} sentences...'.format(len(funs)))
    # cbow is default
    model = word2vec.Word2Vec(funs, size=700, min_count=20, window=20, compute_loss=True)
    model.init_sims(replace=True)
    logger.info('Loss is {}'.format(model.get_latest_training_loss()))
    save_model(model, config['fun2vec']['model'])

@manager.option('-m', '--model', dest='model_name', default='fun2vec')
@manager.option('-n', '--topn', dest='topn', default=300)
@manager.option('-w', '--target_word', dest='target_word', default=None)
def check_vocab(model_name, topn, target_word):
    'Check model vocabrary in frequent order'
    logging.getLogger().setLevel(logging.ERROR)
    model = load_model(model_name).wv
    if target_word:
        print(model.vocab[target_word].count, target_word)
    else:
        for idx, word in enumerate(model.index2word):
            print(model.vocab[word].count, word)
            if idx >= int(topn):
                break

def save_model(model, file_path):
    with gzip.open(file_path, 'wb') as f:
        pickle.dump(model, f, protocol=2)
    logger.info('Saved model in {}'.format(file_path))

def load_model(model_name):
    model = word2vec.Word2Vec.load(config[model_name]['model'], mmap=None)
    print(model_name.center(70, '-'))
    print('corpus size:', str(model.corpus_count // 10000) + '万')
    print('vocab size:', '{:,}'.format(len(model.wv.vocab)))
    print('loss:', str(model.get_latest_training_loss() // 10000) + '万')
    # memory friendly
    return model.wv

def main(args):
    model_name = args.model
    topn = int(args.topn)
    restrict_vocab = int(args.restrict_vocab) if args.restrict_vocab else None
    models = OrderedDict()
    if model_name in ['word2vec', 'all']:
        models['word2vec'] = load_model('word2vec')
    if model_name in ['fun2vec', 'all']:
        models['fun2vec_clustered'] = load_model('fun2vec_clustered')
    try:
        while True:
            text = prompt('words> ', history=history)
            if not text:
                continue
            if text == 'exit':
                raise KeyboardInterrupt
            for name, model in models.items():
                try:
                    print(name.center(70, '-'))
                    for word, sim in model.most_similar(positive=text.split(), topn=topn, restrict_vocab=restrict_vocab):
                        word = ljust_ja(word, 20)
                        sim = round(sim, 3)
                        print(highlight('{word} {sim:.3f}'.format(word=word, sim=sim), \
                            lexer=CustomLexer(), formatter=Terminal256Formatter(style=get_color_style(sim))), end='')
                        highlight.__init__()
                except KeyError as e:
                    print(e.args[0])
                    continue
    except (EOFError, KeyboardInterrupt):
        print('\nExit.')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Show similar words/funs')
    parser.add_argument('-m', '--model', default='all', help='specify which model to use')
    parser.add_argument('-n', '--topn', default=10, help='specify the number of output')
    parser.add_argument('-rv', '--restrict_vocab', default=None, help='specify how the number of word vectors you will check in the vocabulary order')
    args = parser.parse_args()

    from prompt_toolkit.history import FileHistory
    from prompt_toolkit import prompt
    from pygments import highlight
    from pygments.formatters import Terminal256Formatter
    from util import ljust_ja, CustomLexer, get_color_style

    history = FileHistory('./.model_test_history')

    logging.getLogger().setLevel(logging.ERROR)
    main(args)
