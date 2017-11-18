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
from util import load_config, _pickle, _unpickle

logging.config.dictConfig(load_config('log'))
_logger = logging.getLogger(__name__)
config = load_config('file')

"""
Knowledge of Gensim
・model.wv.syn0normとmodel.wv.index2wordは対応関係にある
・model.wv.vocab['アニメ'].index -> index取得
・複数単語のベクトルをまとめて取得するときはmodel.wv[['アニメ', 'オタク']]
・model.wv.index2word[0] -> 'アニメ' 単語取得
"""

class Model:
    @classmethod
    def create(cls, model_name, size=700, min_count=30, window=5, compute_loss=True):
        sentences = _unpickle(config['corpus'][model_name])
        _logger.info(f'Creating word2vec model from {len(sentences)} sentences...')
        # cbow is default
        model = word2vec.Word2Vec(sentences, size=size, min_count=min_count, window=window, compute_loss=compute_loss)
        model.init_sims(replace=True) # trim unneeded model memory by L2-norm
        _logger.info(f'Loss is {model.get_latest_training_loss()}')
        cls._save_model(model, config['model'][model_name])

    @staticmethod
    def _save_model(model, file_path):
        _pickle(model, file_path) # edit protocol later if error occurs
        _logger.info(f'Saved model in {file_path}')

    @staticmethod
    def load_model(model_name):
        model = word2vec.Word2Vec.load(config['model'][model_name], mmap=None)
        print(model_name.center(70, '-'))
        print('corpus size:', str(model.corpus_count // 10000) + '万')
        print('vocab size:', '{:,}'.format(len(model.wv.vocab)))
        print('loss:', str(model.get_latest_training_loss() // 10000) + '万')
        # memory friendly
        return model.wv

manager = Manager(usage='Create word2vec/fun2vec model')
@manager.command
def create_word2vec():
    Model.create('word2vec')

@manager.command
def create_fun2vec():
    Model.create('fun2vec', min_count=20, window=10)

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

def test_visualize(wv):
    """
    ref: http://projector.tensorflow.org/
    """
    import pandas as pd
    df_wv = pd.DataFrame([wv.word_vec(w) for w in wv.index2word])
    df_meta = pd.DataFrame(wv.index2word)

    df_wv.to_csv('data/wv.tsv', sep='\t', header=False, index=False)
    df_meta.to_csv('data/metadata.tsv', sep='\t', header=False, index=False)

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
