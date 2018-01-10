import os
import json, yaml
import logging
import logging.config
import pickle, gzip
from flask_script import Manager
from pygments.lexer import RegexLexer
import re
from pygments.token import Token, String, Number
from pygments.style import Style

def load_config(name):
    with open(os.path.join(os.path.dirname(__file__), 'config', name + '_config.yml'), 'r') as f:
        config = yaml.load(f)
        return config

logging.config.dictConfig(load_config('log'))
_logger = logging.getLogger(__name__)

def _unpickle(file_name, compress=True):
    assert os.path.exists(file_name), f'{file_name} does not exist'
    _logger.info(f'unpickle {file_name}')
    if compress:
        with gzip.open(file_name, 'rb') as f:
            return pickle.load(f)
    else:
        with open(file_name, 'rb') as f:
            return pickle.load(f)


def _pickle(objects, file_name, compress=True, protocol=pickle.HIGHEST_PROTOCOL):
    _logger.info(f'pickle {file_name}')
    if compress:
        with gzip.open(file_name, 'wb') as f:
            pickle.dump(objects, f, protocol=protocol)
    else:
        with open(file_name, 'wb') as f:
            pickle.dump(objects, f, protocol=protocol)

def find_close_words():
    import difflib
    import pandas as pd
    from model import Model
    result = []
    model = load_model('word2vec').wv
    model_fun2vec = load_model('fun2vec').wv
    logger.info('Find close words...')
    vocab = model.index2word
    for idx, word in enumerate(model_fun2vec.index2word, 1):
        close_words = difflib.get_close_matches(word, vocab)
        if len(close_words) >= 2:
            close_words = close_words[1:]
            for close_word in close_words:
                try:
                    sim = model.similarity(word, close_word)
                    if sim > 0.6:
                        if model.vocab[word].count > model.vocab[close_word].count:
                            result.append([word, close_word, sim])
                        else:
                            result.append([close_word, word, sim])
                except KeyError:
                    pass
        if idx % 1000 == 0:
            logger.info('{} Finished'.format(idx))
    df = pd.DataFrame(result, columns=['replace_word', 'word', 'similarity'])
    for row in df[df.replace_word.isin(df.word)].itertuples():
        df.set_value(df[df.replace_word == row.replace_word].index[0], 'replace_word',\
            df[df.word == row.replace_word].replace_word.values[0])
    df.drop_duplicates(subset=['replace_word', 'word'], inplace=True)
    df.to_csv('data/close_word.tsv', index=False)

def read_sql(file_path):
    with open(file_path, 'r') as f:
        sql = f.read()
    return sql

def read_secrets(key):
    FILE_SECRETS = os.path.join('config', 'secrets.yml')
    with open(FILE_SECRETS, 'r') as f:
        data = yaml.load(f)
    return data.get(key)

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
