from util import read_secrets
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, BigInteger, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import sessionmaker
from flask_script import Manager, prompt_bool
from datetime import datetime

db_secret = read_secrets('mysql')
db_url = 'mysql+pymysql://{user}:{password}@localhost/{db_name}?charset=utf8mb4&local_infile=1'.format(**db_secret)
engine = create_engine(db_url)
Base = declarative_base()

def create_session():
    Session = sessionmaker(bind=engine)
    return Session()

class User(Base):
    """
    Table of twitter users
    """
    __tablename__ = 'users'
    id                    = Column(BigInteger, primary_key=True, autoincrement=False, comment='twitter unique id')
    screen_name           = Column(String(100), nullable=False, comment='screen_names are unique but subject to change')
    description           = Column(Text, nullable=False, comment='profile description')
    default_profile_image = Column(Boolean, nullable=True, comment='When true, the user has not uploaded their own image')
    followers_count       = Column(Integer, nullable=True, comment='the number of followers')
    friends_count         = Column(Integer, nullable=True, comment='The number of users the user is following')
    statuses_count        = Column(Integer, nullable=True, comment='The number of Tweets (including retweets) issued by the user')
    favourites_count      = Column(Integer, nullable=True, comment='The number of Tweets this user has liked in the account’s lifetime')
    verified              = Column(Boolean, nullable=True, comment='When true, indicates that the user has a verified account')
    created_at            = Column(DateTime, nullable=False, default=datetime.now)
    updated_at            = Column(DateTime, nullable=False, onupdate=datetime.now)

    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.screen_name           = kwargs['screen_name']
        self.description           = kwargs['description']
        self.default_profile_image = kwargs['default_profile_image']
        self.followers_count       = kwargs['followers_count']
        self.friends_count         = kwargs['friends_count']
        self.statuses_count        = kwargs['statuses_count']
        self.favourites_count      = kwargs['favourites_count']
        self.verified              = kwargs['verified']
        self.created_at            = datetime.now()
        self.updated_at            = datetime.now()

    def __repr__(self):
        return '<User id={id} screen_name={screen_name} description={description}>'.format(
                id=self.id, screen_name=self.screen_name, description=self.description)

class Friend(Base):
    """
    Table of the relationships between the user and his/her friend.
    """
    __tablename__ = 'friends'
    user_id      = Column(BigInteger, primary_key=True, autoincrement=False, comment='user unique id')
    friend_id    = Column(BigInteger, primary_key=True, autoincrement=False, comment='friend unique id')
    created_at   = Column(DateTime, nullable=False, default=datetime.now)
    updated_at   = Column(DateTime, nullable=False, onupdate=datetime.now)

    def __init__(self, **kwargs):
        self.user_id    = kwargs['user_id']
        self.friend_id  = kwargs['friend_id']
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def __repr__(self):
        return f'<user_id={self.user_id} friend_id={self.friend_id}>'

manager = Manager(usage='Perform database operations')
@manager.option('-t', '--table_name', dest='table_name', default=None)
def init_db(table_name=None):
    """
    Initialize DB or table
    """
    if table_name:
        if prompt_bool(f'Are you sure you want to initialized table of {table_name}'):
            Base.metadata.tables[table_name].create(bind=engine)
    elif prompt_bool('Are you sure you want to initialized database'):
        Base.metadata.create_all(engine)
