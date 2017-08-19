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
    corpus = []
    session = create_session()
    logger.info('Fetching twitter profile data from DB...')
    res = session.query(User.description).filter(User.verified==0).all() # 公式アカウントは除く
    logger.info('Fetched {} twitter profiles'.format(res.count()))
    logger.info('Extracting words from twitter profiles...')
    STOP_WORDS = pd.read_csv(FILE_STOP_WORDS, header=None).values.flatten().tolist()
    for idx, profile in enumerate(res, 1):
        profile = profile[0]
        if profile is None:
            continue
        words = extract_words(profile, STOP_WORDS)
        if len(words) > 0:
            corpus.append(words)
        if idx % 10000 == 0:
            logger.info('Finished {} records'.format(idx))
    with open(FILE_CORPUS, 'wb') as f:
        pickle.dump(corpus, f)
    logger.info('Saved corpus of {} sentences in {}'.format(len(corpus), FILE_CORPUS))

if __name__ == '__main__':
    create_corpus()
