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
    logger.info('Creating word2vec model...')
    model = word2vec.Word2Vec(sentences, size=500, min_count=30, window=5)
    save_model(model, config['word2vec']['model'])

@manager.command
def create_fun2vec():
    'Create fun2vec model'
    with gzip.open(config['fun2vec']['corpus'], 'rb') as f:
        sentences = pickle.load(f)
    # defaultでcbowらしい
    model = word2vec.Word2Vec(sentences, size=500, min_count=20, window=5)
    save_model(model, config['fun2vec']['model'])

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

def save_model(model, file_path):
    with gzip.open(file_path, 'wb') as f:
        pickle.dump(model, f, protocol=2)
    logger.info('Saved model in {}'.format(file_path))

def load_model(model_name):
    return word2vec.Word2Vec.load(config[model_name]['model'], mmap=None)

def main(args):
    model_name = args.model
    topn = int(args.topn)
    restrict_vocab = int(args.restrict_vocab) if args.restrict_vocab else None
    models = OrderedDict()
    if model_name in ['word2vec', 'all']:
        models['word2vec'] = load_model('word2vec')
    if model_name in ['fun2vec', 'all']:
        models['fun2vec'] = load_model('fun2vec')
    try:
        while True:
            text = prompt('words> ', history=history)
            if not text:
                continue
            for name, model in models.items():
                try:
                    print('--------------', name, '--------------')
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
    from pygments.lexer import RegexLexer
    from pygments.formatters import Terminal256Formatter
    from pygments.style import Style
    from pygments.token import Token, String, Number
    import re

    history = FileHistory('./.model_test_history')

    def ljust_ja(text, length):
        text_length = 0
        for char in text:
            if ord(char) <= 255:
                text_length += 1
            else:
                text_length += 2

        return text + (length - text_length) * ' '

    class CustomLexer(RegexLexer):
        flags = re.IGNORECASE
        tokens = {
            'root': [
                (r'^[^\W]+',    String),
                (r'0\.[0-9]+$', Number)
            ]
        }

    def get_color_style(sim):
        SIM_COLORS = {
            'low':          '#b22222',
            'normal':       '#00bfff',
            'high':         '#ansiteal',
            'extreme_high': '#ansiturquoise'
        }
        sim_color = None
        if sim >= 0.9:
            sim_color = SIM_COLORS['extreme_high']
        elif sim >= 0.8:
            sim_color = SIM_COLORS['high']
        elif sim >= 0.7:
            sim_color = SIM_COLORS['normal']
        else:
            sim_color = SIM_COLORS['low']

        class ColorStyle(Style):
            styles = {
                Token.String: '#ff8c00',
                Token.Number: sim_color
            }
        return ColorStyle

    logging.getLogger().setLevel(logging.ERROR)
    main(args)
