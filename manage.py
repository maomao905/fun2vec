from flask import Flask
from flask_script import Manager
from model import manager as db_manager
from util import manager as util_manager
from fun2vec import manager as fun2vec_manager
from api.twitter import manager as twitter_manager

app = Flask(__name__)
manager = Manager(app)

manager.add_command('db', db_manager)
manager.add_command('util', util_manager)
manager.add_command('fun2vec', fun2vec_manager)
manager.add_command('twitter', twitter_manager)

if __name__ == "__main__":
    manager.run()
