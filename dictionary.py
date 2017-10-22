import pandas as pd
import MeCab
import os
import logging
from util import load_config
from flask_script import Manager

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
    for row in df_new_word.itertuples():
        morph = create_morph(row.surface, row.lexical, row.speech)
        if morph:
            res.append(morph + '\n')

    with open(FILE_OUTPUT, 'w') as f:
        f.writelines(res)

    compile_dictionary()
    logger.info('New words added to dictionary')

    df_close_word = pd.read_csv(FILE_CLOSE_WORD)
    for row in df_close_word.itertuples():
        morph = replace_morph(row.word, row.replace_word)
        if morph:
            res.append(morph + '\n')

    df_close_word_original = pd.read_csv(FILE_CLOSE_WORD_ORIGINAL)
    for row in df_close_word_original.itertuples():
        morph = replace_morph(row.word, row.replace_word)
        if morph:
            res.append(morph + '\n')

    with open(FILE_OUTPUT, 'w') as f:
        f.writelines(res)
    logger.info(f'Created original dictionary in {FILE_OUTPUT}')
    compile_dictionary()
    logger.info(f'Original dictionary compiled!')

def create_morph(surface, lexical, speech):
        return f'{surface},,,1,名詞,固有名詞,一般,*,*,*,{lexical},{speech},{speech}'

def replace_morph(word, replace_word):
    if word != word or word == replace_word:
        return
    tagger = MeCab.Tagger(f"--dicdir={file_config['mecab']['dicdir']} --userdic={file_config['mecab']['userdic']}")
    tagger.parse('')
    node = tagger.parseToNode(word)
    while node:
        if node.surface:
            features = node.feature.split(',')
            features[6] = replace_word
        node = node.next
    return f'{word},,,1,' + ','.join(features)

def compile_dictionary():
    import subprocess
    import sys
    command = f"/usr/local/Cellar/mecab/0.996/libexec/mecab/mecab-dict-index \
    -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd \
    -u {file_config['mecab']['userdic']} \
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

if __name__ == '__main__':
    create_original_dictionary()
