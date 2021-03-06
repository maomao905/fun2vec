import os, sys
sys.path.append(os.getcwd())
from db import User, Friend, create_session, bulk_save
from sqlalchemy import text
import requests
from requests_oauthlib import OAuth1
from util import read_secrets, read_sql, load_config, _unpickle
import json
import logging
from pprint import pprint
from time import sleep
from flask_script import Manager

class Twitter:
    __ENDPOINT_STATUS_FILTER = 'https://stream.twitter.com/1.1/statuses/filter.json'
    __ENDPOINT_STATUS_UPDATE = 'https://api.twitter.com/1.1/statuses/update.json'
    __COLUMNS_USER = User.__table__.columns.keys()
    def __init__(self):
        self._session = create_session()
        self._auth = self.__get_auth()
        logging.config.dictConfig(load_config('log'))
        self._logger = logging.getLogger(__name__)

    def _request(self, endpoint, params, method='GET', stream=False, timeout=300):
        res = requests.request(
            method=method.upper(),
            url=endpoint,
            auth=self._auth,
            stream=stream,
            params=params,
            timeout=timeout,
        )

        if res.ok:
            return res
        else:
            self._logger.error('Requst to Twitter API failed')
            if res.reason == 'Authorization Required': # Unauthorized account
                return res.reason
            res.raise_for_status()

    @classmethod
    def _extract_user_info(cls, info):
        user_info = {k: v for k, v in info['user'].items() if k in cls.__COLUMNS_USER}
        retweet_user_info = {k: v for k, v in info.get('retweeted_status', {}).get('user', {}).items() if k in cls.__COLUMNS_USER}
        return user_info, retweet_user_info

    def search(self, keywords):
        """search keywords from realtime tweets
        ref: https://developer.twitter.com/en/docs/tweets/filter-realtime/api-reference/post-statuses-filter.html

        :param keywords: specified by a comma-separated list
        """
        res = self._request(
            method='POST',
            endpoint=self.__ENDPOINT_STATUS_FILTER,
            params={
                'track': keywords,
                'language': 'ja',
                'stall_warnings': True,
            },
            stream=True
        )
        return res

    def send(self, text, reply_to=None):
        """tweet
        :param text: if reply_to specified, this must include @username.
        :param reply_to: if specified, reply to the specified tweet id.
        """
        if reply_to:
            assert '@' in text, '@username must be included in the text when you reply.'

        res = self._request(
            method='POST',
            endpoint=self.__ENDPOINT_STATUS_UPDATE,
            params={
                'status': text,
                'in_reply_to_status_id': reply_to,
            }
        )

    def _save_users(self, store_users):
        """
        users: list of User object
        """
        res = self._session.query(User.id).filter(User.id.in_(list(store_users.keys()))).all()
        exist_users = [r[0] for r in res]
        new_users = []
        for user_id, user_info in store_users.items():
            if user_id not in exist_users and User.valid(user_info):
                new_users.append(User(**user_info))
        self._session.bulk_save_objects(new_users)
        self._session.commit()

    @staticmethod
    def __get_auth():
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
def scrape_user():
    """
    Scrape Twitter profile data
    """
    t = Twitter()
    t._logger.info('Requsting to Twitter API...')
    res = t._request(
        endpoint='https://stream.twitter.com/1.1/statuses/sample.json',
        params={
            'language': 'ja', # only Japanese
            'stall_warnings': True # api rate limitを伝えてくれる
        },
        stream=True,
    )

    if res.ok:
        store_users = {}
        for idx, line in enumerate(res.iter_lines(), 1):
            try:
                if line:
                    info = json.loads(line.decode('utf-8'))
                    # save users in DB
                    for user_info in t._extract_user_info(info):
                        if user_info and user_info['id'] not in store_users:
                            store_users.update({user_info['id']: user_info})
                    if len(store_users) >= 200:
                        t._save_users(store_users)
                        store_users = {}
                    if idx % 5000 == 0:
                        t._logger.info(f'Go through {idx} users')
            except Exception as e:
                t._logger.error(e)
                sleep(15*60)
                continue
    else:
        t._logger.error('Requst to Twitter API failed')
        res.raise_for_status()

@manager.command
def scrape_friends():
    """
    Scrape following relationships.
    1. Iterate over users who have less than 2 funs order by friends_count
    2. Call friends/ids API to get frield list
    Twitter API
        - ref: https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-friends-ids
        - limit: 15 times per 15 mins
    """
    FILE_SQL = 'sql/get_users_not_in_friends.sql'
    API_FRIENDS_URL = 'https://api.twitter.com/1.1/friends/ids.json'
    t = Twitter()
    config_file = load_config('file')
    corpus = _unpickle(config_file['corpus']['fun2vec'])
    while True:
        try:
            t._logger.info('Running query to fetch users...')
            stmt = text(read_sql(FILE_SQL))
            stmt = stmt.columns(User.id)
            res = t._session.execute(stmt).fetchall()
            if len(res) == 0:
                t._logger.info('Scraped all friends! Done!')
                t._session.close()
                break
            for idx, user in enumerate(res, 1):
                funs = corpus.get(user.id, set())
                if len(funs) >= 2:
                    # insert -1 if the user already have more than 2 funs to check which users
                    # it has already covered
                    t._session.add(Friend(user_id=user.id, friend_id=-1))
                    t._session.commit()
                    t._logger.info(f'<user_id: {user.id}> Skipped')
                    continue

                response = t._request(
                    endpoint=API_FRIENDS_URL,
                    params={
                        'user_id':     user.id,
                        'language':    'ja',
                        'count':       5000,
                    },
                )
                if response == 'Authorization Required':
                    # insert -199 in case when the user account is not authorized.
                    t._session.add(Friend(user_id=user.id, friend_id=-199))
                    t._session.commit()
                    t._logger.info(f'<user_id: {user.id}> The user is not authorized')
                else:
                    friend_ids = response.json()['ids']
                    if len(friend_ids) == 0:
                        # insert -99 in case when the user has no friends
                        # (rarely occurs though since it has already checked)
                        t._session.add(Friend(user_id=user.id, friend_id=-99))
                        t._session.commit()
                    else:
                        # store friends
                        friends = [Friend(user_id=user.id, friend_id=id_) for id_ in friend_ids]
                        bulk_save(t._session, friends)
                        t._logger.info(f'<user_id: {user.id}> Add {len(friends)} friends')

                sleep(60) # avoid rate limit
        except Exception as e:
            t._logger.error(e)
            if t._session.is_active:
                t._session.rollback()
            else:
                t._session.commit()
                t._session.close()
            break

@manager.command
def geo_search():
    URL = 'https://api.twitter.com/1.1/geo/reverse_geocode.json'
    t = Twitter()
    t._logger.info('Requsting to Twitter API...')
    res = t._request(
        endpoint=URL,
        params={
            'language': 'ja', # only Japanese
            'granularity': 'poi',
            'lat': 35.455865,
            'long': 139.633103,
            'accuracy': 5000,
            'max_results': 30,
        },
    ).json()
