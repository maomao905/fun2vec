import MeCab
import re
import logging
from util import load_config
import pandas as pd

logging.config.dictConfig(load_config('log'))
logger = logging.getLogger(__name__)

REGEX_JA = re.compile(r'[ぁ-んァ-ン一-龥]')
REGEX_EN = re.compile(r'[a-z]+', re.IGNORECASE)
REGEX_STOP_CHAR = re.compile(r'^([ァ-ン]|[ぁ-ん]{1,2})$', re.IGNORECASE)

UNKNOWN_MARK = '*'

config_mecab = load_config('file')['mecab']
STOP_WORDS = pd.read_csv(config_mecab['stop_words'], header=None).values.flatten().tolist()

def extract_words(sentence):
    """
    日本語で名詞 or 形容詞を取得
    """
    tagger = MeCab.Tagger('--dicdir={} --userdic={}'.format(config_mecab['dicdir'], config_mecab['userdic']))
    tagger.parse('')
    node = tagger.parseToNode(sentence)
    words = []
    while node:
        if node.surface != '':
            # 品詞
            features = node.feature.split(',')
            if filter_feature(features):
                genkei = features[6]

                if valid_genkei(genkei, STOP_WORDS):
                    words.append(genkei)
        node = node.next
    return words

def valid_genkei(genkei, stop_words):
    """
    原型をチェック
    英語・カタカナ１文字だけ、ひらがな１文字or２文字は省く
    """
    return (not bool(REGEX_STOP_CHAR.match(genkei)) and genkei != UNKNOWN_MARK \
        and genkei not in stop_words)

def check_ja(text):
    """
    日本語かを判定
    """
    return bool(REGEX_JA.match(text))

def check_en(text):
    """
    英語かを判定
    """
    return bool(REGEX_EN.search(text))

def filter_feature(features):
    if features[0] == '名詞' and features[1] in ['一般', 'サ変接続', '固有名詞']:
        if features[2] == '地域':
            return False
        return True
    else:
        return False

def find_close_words():
    import difflib
    import pandas as pd
    from fun2vec import load_model
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

if __name__ == '__main__':
    create_original_dictionary()
    # replace_morph('寿司', 'お寿司')
