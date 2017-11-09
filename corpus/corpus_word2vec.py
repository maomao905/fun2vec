from corpus.corpus_base import BaseCorpus
from db import create_session, User

class Word2vecCorpus(BaseCorpus):
    def extract(self):
        corpus = []
        session = create_session()
        logger.info('Running query and Extracting words...')
        try:
            for idx, user in enumerate(session.query(User.description).filter(User.verified==0).yield_per(500), 1):
                profile = user.description
                # url置き換え
                profile = self._replace_url(profile)
                # 単語取得
                words = self.__word.preprocess(profile)
                if len(words) >= 2:
                    corpus.append(words)

                if idx % 10000 == 0:
                    logger.info(f'Finished {idx} profiles')

            with gzip.open(config['word2vec']['corpus'], 'wb') as f:
                pickle.dump(corpus, f)
            logger.info(f"Saved corpus of {len(corpus)} sentences in {config['word2vec']['corpus']}")
        except Exception as e:
            logger.error(e)
        finally:
            session.close()
