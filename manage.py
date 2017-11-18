from flask import Flask
from flask_script import Manager
from db import manager as db_manager
from model import manager as model_manager
from api.twitter import manager as twitter_manager
from corpus.corpus_word2vec import manager as corpus_word2vec_manager
from corpus.corpus_fun2vec import manager as corpus_fun2vec_manager
from dictionary import manager as dictionary_manager

app = Flask(__name__)
manager = Manager(app)

manager.add_command('db', db_manager)
manager.add_command('model', model_manager)
manager.add_command('twitter', twitter_manager)
manager.add_command('word2vec_corpus', corpus_word2vec_manager)
manager.add_command('fun2vec_corpus', corpus_fun2vec_manager)
manager.add_command('dictionary', dictionary_manager)

if __name__ == "__main__":
    manager.run()
