import MeCab
import re
from model import User, create_session
import logging

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s][%(levelname)-5s][%(name)-10s][%(funcName)-10s] %(message)s')
logger = logging.getLogger(__name__)

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
            if filter_feature(features) and check_ja(node.surface):
                # 原形が取得できない場合
                if features[6] == '*':
                    words.append(node.surface)
                else:
                    # 原形を取得
                    words.append(features[6])
        node = node.next
    return words

def check_ja(surface):
    """
    日本語かを判定
    """
    pattern = r"[ぁ-んァ-ン一-龥]"
    ja = re.compile(pattern)
    if ja.match(surface):
        return True
    else:
        return False

def filter_feature(features):
    if features[0] == '名詞' and features[1] not in ['代名詞', '数']:
        return True
    elif features[0] == '形容詞':
        return True
    else:
        return False

def save(words):
    """
    分かち書きしたものを保存
    """
    FILE_WAKATI = 'wakati.txt'
    with open(FILE_WAKATI, 'w') as f:
        for w in words:
            f.writelines(' '.join(w))
    logger.info('Saved {} wakti sentences in {}'.format(len(words), FILE_WAKATI))

def create_wakati():
    words = []
    session = create_session()
    logger.info('Fetching twitter profile data from DB...')
    res = session.query(User.description).all()
    logger.info('Extracting words from twitter profile...')
    SEP_LENGTH = 100 # 長すぎるとsengmentation failedになるので100で区切り、新しい文章とする
    for profile in res:
        profile = profile[0]
        if profile is None:
            continue
        for i in range(0, len(profile), SEP_LENGTH):
            words.append(extract_words(profile[i:i+SEP_LENGTH]))
    save(words)
