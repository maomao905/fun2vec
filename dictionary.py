import pandas as pd
import MeCab
import os
import logging
from util import load_config
from flask_script import Manager
from morpheme import WordParser

"""
Create original dictionary
Merge new_word.tsv + close_word.tsv + close_word_original.tsv
Final output: original_dict.csv
"""
logging.config.dictConfig(load_config('log'))
logger = logging.getLogger(__name__)

file_config = load_config('file')

DIR_DICTIONARY = 'data/dictionary'
FILE_OUTPUT = os.path.join(DIR_DICTIONARY, 'original_dic.csv')
FILE_NEW_WORD = os.path.join(DIR_DICTIONARY, 'new_word.csv')
FILE_CLOSE_WORD = os.path.join(DIR_DICTIONARY, 'close_word.csv')
FILE_CLOSE_WORD_ORIGINAL = os.path.join(DIR_DICTIONARY, 'close_word_original.csv')

manager = Manager(usage='Perform dictionary operations')
@manager.command
def create_original_dictionary():
    """
    Create original dictionary
    """
    res = []

    df_new_word = pd.read_csv(FILE_NEW_WORD)
    df_new_word = df_new_word.assign(
        cost=lambda df: df.cost.fillna(1).astype(int),
        pos1=lambda df: df.pos1.fillna('名詞'),
        pos2=lambda df: df.pos2.fillna('固有名詞'),
        pos3=lambda df: df.pos3.fillna('一般'),
    )
    for _, row in df_new_word.iterrows():
        morph = create_morph(**row.to_dict())
        if morph:
            res.append(morph + '\n')

    with open(FILE_OUTPUT, 'w') as f:
        f.writelines(res)

    compile_dictionary()
    logger.info('New words added to dictionary')

    file_config = load_config('file')
    __NODE = {
        'keys':         ('features', 'cost'),
        'node-format':  ('%H',       '%pw'),
        'unk-format':   ('%H',       '%pw'),
    }
    parser = WordParser(**file_config['mecab'], node=__NODE)

    for file_path in (FILE_CLOSE_WORD, FILE_CLOSE_WORD_ORIGINAL):
        df_close_word = pd.read_csv(file_path)
        for row in df_close_word.itertuples():
            morph = replace_morph(parser, row.word, row.replace_word)
            if morph:
                res.append(morph + '\n')

    with open(FILE_OUTPUT, 'w') as f:
        f.writelines(res)
    logger.info(f'Created original dictionary in {FILE_OUTPUT}')
    compile_dictionary()
    logger.info(f'Original dictionary compiled!')

def create_morph(**kwargs):
    return '{surface},,,{cost},{pos1},{pos2},{pos3},*,*,*,{lexeme},{speech},{speech}'.format_map(kwargs)

def replace_morph(parser, word, replace_word):
    if word != word or word == replace_word:
        return
    morphs = parser(word)
    assert len(morphs) == 1, f'{word} is splited into more than one word'
    morph = morphs[0]
    features = morph.features.split(',')
    features[6] = replace_word
    # substract 100 from the original cost
    cost = int(morph.cost) - 100
    return f'{word},,,{cost},' + ','.join(features)

def compile_dictionary():
    import subprocess
    import sys
    command = f"/usr/local/Cellar/mecab/0.996/libexec/mecab/mecab-dict-index \
    -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd \
    -u {file_config['mecab']['userdics'][0]} \
    -f utf-8 \
    -t utf-8 \
    data/dictionary/original_dic.csv"
    res = subprocess.run(command.split(), stdout=subprocess.PIPE)
    if res.returncode == 0:
        logger.info('Dictionary compiled successfully')
    else:
        raise('Dictionary compile failed')


def cut():
    FILE_TEMP_OUTPUT = 'data/dictionary/close_word_v2.csv'
    res = []
    df_close_word = pd.read_csv(FILE_CLOSE_WORD)
    for row in df_close_word.itertuples():
        if row.similarity > 0.75:
            res.append([row.replace_word, row.word, row.similarity])

    df_res = pd.DataFrame(res, columns=df_close_word.columns).sort_values(by='similarity')
    df_res.to_csv(FILE_TEMP_OUTPUT, index=False)
