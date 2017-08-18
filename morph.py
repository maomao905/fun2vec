import MeCab
import re
import logging

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s][%(levelname)-5s][%(name)-10s][%(funcName)-10s] %(message)s')
logger = logging.getLogger(__name__)

REGEX_JA = re.compile(r'[ぁ-んァ-ン一-龥]')
REGEX_HIRA = re.compile(r'^[ぁ-ん]{2}$')
REGEX_EN = re.compile(r'[a-zA-Z]+')

UNKNOWN_MARK = '*'
def extract_words(sentence, stop_words=[]):
    """
    日本語で名詞 or 形容詞を取得
    """
    tagger = MeCab.Tagger('mecabrc -d /usr/local/lib/mecab/dic/ipadic')
    tagger.parse('')
    node = tagger.parseToNode(sentence)
    words = []
    while node:
        if node.surface != '':
            # 品詞
            features = node.feature.split(',')
            if filter_feature(features) and check_ja(node.surface):
                try:
                    genkei = features[7] if check_en(features[6]) else features[6]
                except IndexError:
                    # genkei[7]が存在しない場合
                    genkei = features[6]

                if valid_genkei(genkei, stop_words):
                    words.append(genkei)
        node = node.next
    return words

def valid_genkei(genkei, stop_words):
    """
    原型をチェック
    １文字だけ、ひらがな２文字は省く
    """
    return (not bool(REGEX_HIRA.match(genkei)) and genkei != UNKNOWN_MARK \
        and len(genkei) > 1 and genkei not in stop_words)

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
    # 固有名詞も省いてみる
    if features[0] == '名詞' and features[1] in ['一般', 'サ変接続']:
        return True
    else:
        return False
