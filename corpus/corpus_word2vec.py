from corpus.corpus_base import BaseCorpus
from db import create_session, User
from util import load_config, _pickle
from flask_script import Manager
import logging

class Word2vecCorpus(BaseCorpus):
    def __init__(self):
        super().__init__()
        logging.config.dictConfig(load_config('log'))
        self._logger = logging.getLogger(__name__)

    def extract(self, text):
        text = self._replace_url(text)
        return self._word.preprocess(text)

manager = Manager(usage='Perform word2vec corpus operations')
@manager.command
def create_word2vec_corpus():
    corpus = []
    session = create_session()
    wc = Word2vecCorpus()

    try:
        for idx, user in enumerate(session.query(User.description).filter(User.verified==0).yield_per(500), 1):
            words = wc.extract(user.description)
            if len(words) >= 2:
                corpus.append(words)

            if idx % 10000 == 0:
                wc._logger.info(f'Finished {idx} profiles')
    except Exception as e:
        wc._logger.error(e)
    finally:
        session.close()
    _pickle(corpus, wc._config_file['word2vec'])
    wc._logger.info(f"Saved corpus of {len(corpus)} sentences in {wc._config_file['word2vec']}")
