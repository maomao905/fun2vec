import MeCab
import re
import logging
from util import load_config
import pandas as pd

logging.config.dictConfig(load_config('log'))
logger = logging.getLogger(__name__)

REGEX_JA = re.compile(r'[ぁ-んァ-ン一-龥]')
REGEX_EN = re.compile(r'[a-z]+', re.IGNORECASE)
REGEX_STOP_CHAR = re.compile(r'^([ァ-ン一-龥]|[ぁ-ん]{1,2}|[a-z]+)$', re.IGNORECASE)

UNKNOWN_MARK = '*'

config = load_config('file')
STOP_WORDS = pd.read_csv(config['stop_words'], header=None).values.flatten().tolist()

def extract_words(sentence):
    """
    日本語で名詞 or 形容詞を取得
    """
    tagger = MeCab.Tagger()
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
        if features[2] in ['地域', '人名']:
            return False
        return True
    else:
        return False

def find_close_words():
    import difflib
    from fun2vec import load_model
    model = load_model('fun2vec')
    # model.vocab
    logger.info('Find close words...')
    vocab = model.index2word
    for idx, word in enumerate(model.index2word[-100:], 1):
        # if word is english:
        #     tagger to get katakana
        close_words = difflib.get_close_matches(word, vocab, cutoff=0.4)
        if len(close_words) >= 2:
            print(word, close_words[1:])
        # if idx % 50 == 0:
            # logger.info('{} Finished'.format(idx))



if __name__ == '__main__':
    find_close_words()
