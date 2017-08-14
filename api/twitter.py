import os, sys
sys.path.append(os.getcwd())
from model import User, create_session
import requests
from requests_oauthlib import OAuth1
from util import read_secrets
import json
import logging
from pprint import pprint
from flask_script import Manager

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s][%(levelname)-5s][%(name)-10s][%(funcName)-10s] %(message)s')
logger = logging.getLogger(__name__)

API_URL = 'https://stream.twitter.com/1.1/statuses/sample.json'
# User table column list
COLUMNS = User.__table__.columns.keys()

def extract_user_info(info):
    user_info = {k: v for k, v in info['user'].items() if k in COLUMNS}
    retweet_user_info = {k: v for k, v in info.get('retweeted_status', {}).get('user', {}).items() if k in COLUMNS}
    return user_info, retweet_user_info

def save_user_info(session, user_info):
    """
    プロフィールが存在し、公式アカウントではないもので
    id(primary_key)がDBになければ保存
    """
    if user_info and user_info['description'] and user_info['verified'] == 0:
        if session.query(User).filter_by(id=user_info['id']).count() == 0:
            user = User(**user_info)
            session.add(user)
            session.commit()

manager = Manager(usage='Scraping Twitter profile data')
@manager.command
def scrape():
    'Scrape Twitter profile data from Twitter API'
    secret = read_secrets('twitter')
    auth = OAuth1(
            secret['consumer_key'],
            secret['consumer_secret'],
            secret['access_token'],
            secret['access_token_secret'])

    logger.info('Requsting to Twitter API...')
    params = {
        'language': 'ja', # only Japanese
        'stall_warnings': True # api rate limitを伝えてくれる
    }
    res = requests.get(
        API_URL,
        auth=auth,
        stream=True,
        params=params,
        timeout=30
    )
    if res.ok:
        session = create_session()
        for line in res.iter_lines():
            try:
                if line:
                    info = json.loads(line.decode('utf-8'))
                    # save users in DB
                    for user_info in extract_user_info(info):
                        save_user_info(session, user_info)
            except Exception as e:
                logger.error(e)
                sleep(15*60)
                continue
    else:
        logger.error('Requst to Twitter API failed')
        res.raise_for_status()
