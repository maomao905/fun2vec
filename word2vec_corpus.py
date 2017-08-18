from morph import extract_words
from model import create_session, User
import pickle
import logging
import pandas as pd

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s][%(levelname)-5s][%(name)-10s][%(funcName)-10s] %(message)s')
logger = logging.getLogger(__name__)

FILE_CORPUS = 'data/word2vec_corpus.pkl'
FILE_STOP_WORDS = 'data/stop_words.csv'
def create_corpus():
    from pprint import pprint
    corpus = []
    session = create_session()
    logger.info('Fetching twitter profile data from DB...')
    res = session.query(User.description).filter(User.verified==0).limit(10000) # 公式アカウントは除く
    logger.info('Extracting words from twitter profile...')
    STOP_WORDS = pd.read_csv(FILE_STOP_WORDS, header=None).values.flatten().tolist()
    SEP_LENGTH = 1000 # 長すぎるとsengmentation failedになるので100で区切り、新しい文章とする
    for profile in res:
        words = []
        profile = profile[0]
        if profile is None:
            continue
        for i in range(0, len(profile), SEP_LENGTH):
            result = extract_words(profile[i:i+SEP_LENGTH], STOP_WORDS)
            words.extend(result)
        if len(words) > 0:
            corpus.append(words)
    with open(FILE_CORPUS, 'wb') as f:
        pickle.dump(corpus, f)
    logger.info('Saved corpus of {} sentences in {}'.format(len(corpus), FILE_CORPUS))

if __name__ == '__main__':
    create_corpus()
