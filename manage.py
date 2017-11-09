from flask import Flask
from flask_script import Manager
from db import manager as db_manager
from fun2vec import manager as fun2vec_manager
from api.twitter import manager as twitter_manager
from corpus.corpus_base import manager as corpus_manager
from dictionary import manager as dictionary_manager

app = Flask(__name__)
manager = Manager(app)

manager.add_command('db', db_manager)
manager.add_command('fun2vec', fun2vec_manager)
manager.add_command('twitter', twitter_manager)
manager.add_command('corpus', corpus_manager)
manager.add_command('dictionary', dictionary_manager)

if __name__ == "__main__":
    manager.run()
