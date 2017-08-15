import os, sys
from gensim.models import word2vec
from wakati import create_wakati
from flask_script import Manager
import logging
from pprint import pprint

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s][%(levelname)-5s][%(name)-10s][%(funcName)-10s] %(message)s')
logger = logging.getLogger(__name__)

FILE_MODEL = 'data/profile.model'
FILE_WAKATI = 'data/wakati.txt'

manager = Manager(usage='Create word2vec model')
@manager.command
def create_model():
    'Extract words -> Create wakati sentences -> Create word2vec model'
    create_wakati()
    sentences = word2vec.Text8Corpus(FILE_WAKATI)
    logger.info('Creating word2vec model...')
    model = word2vec.Word2Vec(sentences, size=200, min_count=10, window=5)
    model.save(FILE_MODEL)
    logger.info('Saved model in {}'.format(FILE_MODEL))

def load_model():
    """
    load word2vec model
    """
    return word2vec.Word2Vec.load(FILE_MODEL)

def main(arg):
    logging.getLogger().setLevel(logging.ERROR)
    model = load_model()
    pprint(model.most_similar(positive=arg))

if __name__ == '__main__':
    arg = sys.argv[1:]
    main(arg)
