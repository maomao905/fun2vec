import os, sys
sys.path.append(os.getcwd())
from db import User, Friend, create_session
from sqlalchemy import text
import requests
from requests_oauthlib import OAuth1
from util import read_secrets, read_sql
import json
import logging
from pprint import pprint
from time import sleep
from flask_script import Manager

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s][%(levelname)-5s][%(name)-10s][%(funcName)-10s] %(message)s')
logger = logging.getLogger(__name__)

# User table column list
COLUMNS = User.__table__.columns.keys()

def _extract_user_info(info):
    user_info = {k: v for k, v in info['user'].items() if k in COLUMNS}
    retweet_user_info = {k: v for k, v in info.get('retweeted_status', {}).get('user', {}).items() if k in COLUMNS}
    return user_info, retweet_user_info

def _save_user_info(session, user_info):
    """
    プロフィールが存在し、公式アカウントではないもので
    id(primary_key)がDBになければ保存
    """
    if user_info and user_info['description'] and user_info['verified'] == 0:
        if session.query(User).filter_by(id=user_info['id']).count() == 0:
            user = User(**user_info)
            session.add(user)
            session.commit()

def _get_auth():
    """
    Return Twitter Auth
    """
    secret = read_secrets('twitter')
    return OAuth1(
        secret['consumer_key'],
        secret['consumer_secret'],
        secret['access_token'],
        secret['access_token_secret'])

manager = Manager(usage='Scraping Twitter data')
@manager.command
def scrape_profile():
    """
    Scrape Twitter profile data
    """
    API_URL = 'https://stream.twitter.com/1.1/statuses/sample.json'

    logger.info('Requsting to Twitter API...')
    params = {
        'language': 'ja', # only Japanese
        'stall_warnings': True # api rate limitを伝えてくれる
    }

    res = requests.get(
        API_URL,
        auth=_get_auth(),
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
                    for user_info in _extract_user_info(info):
                        _save_user_info(session, user_info)
            except Exception as e:
                logger.error(e)
                sleep(15*60)
                continue
    else:
        logger.error('Requst to Twitter API failed')
        res.raise_for_status()

@manager.command
def scrape_following():
    """
    Scrape following relationships.
    Additionaly get profile of the users.
    """
    FILE_SQL = 'sql/get_users_not_in_friends.sql'
    while True:
        try:
            session = create_session()
            stmt = text(read_sql(FILE_SQL))
            stmt = stmt.columns(User.id, User.screen_name)
            res = session.execute(stmt).fetchall()
            if len(res) == 0:
                break
            for idx, user in enumerate(res, 1):
                friends = get_friends(user.id, user.screen_name)
                num_profiles = 0
                num_friends = 0
                if len(friends) > 0:
                    for friend in friends:
                        if friend and friend['description'] and friend['verified'] == 0 and friend['lang'] == 'ja':
                            # store profile of new user
                            if session.query(User).filter_by(id=friend['id']).count() == 0:
                                new_user = User(**friend)
                                session.add(new_user)
                                session.commit()
                                num_profiles += 1

                            # store relationships
                            if session.query(Friend).filter_by(user_id=user.id, friend_id=friend['id']).count() == 0:
                                new_friend = Friend(
                                    user_id=user.id,
                                    friend_id=friend['id'],
                                )
                                session.add(new_friend)
                                session.commit()
                                num_friends += 1
                logger.info(f'Add {num_profiles} profiles, Add {num_friends} friends From {len(friends)} friends list')
            session.close()
            sleep(15*60) # avoid rate limit
        except Exception as e:
            logger.error(e)
        finally:
            if session.is_active:
                session.rollback()
            else:
                session.commit()
            session.close()

def get_friends(user_id, screen_name, count=200):
    """
    Get Twitter following users data
    ref: https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-friends-list
    limit: 15 times per 15 mins
    """
    API_FRIENDS_URL = 'https://api.twitter.com/1.1/friends/list.json'

    params = {
        'user_id': user_id,
        'screen_name': screen_name,
        'skip_status': True,
        'language': 'ja',
        'count': count,
    }

    res = requests.get(
        API_FRIENDS_URL,
        auth=_get_auth(),
        params=params,
        timeout=30,
    )

    if res.ok:
        return res.json()['users']
    else:
        logger.error('Requst to Twitter API failed')
        res.raise_for_status()

def test_friend():
    import random
    session = create_session()
    for idx, user in enumerate(session.query(User.id).filter(User.verified==0, User.friends_count>0).limit(2), 1):
        # store relationships
        friend_id = random.randrange(10**5,10**6)
        print(friend_id)
        if session.query(Friend).filter_by(user_id=user.id, friend_id=friend_id).count() == 0:
            new_friend = Friend(
                user_id=user.id,
                friend_id=friend_id,
            )
            session.add(new_friend)
            session.commit()
            break

def test_datetime():
    from datetime import datetime, timedelta
    t = datetime.now() - timedelta(hours=1)
    session = create_session()
    res = session.query(User).filter(User.created_at > t).limit(100)
    print(res.count())
    for user in res:
        print(user.created_at, user.id)

if __name__ == '__main__':
    test_datetime()
