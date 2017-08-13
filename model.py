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

    def __repr__(self):
        return '<User id={id} screen_name={screen_name} description={description}>'.format(
                id=self.id, screen_name=self.screen_name, description=self.description)

manager = Manager(usage='Perform database operations')
@manager.command
def init_db():
    'Create all tables'
    if prompt_bool('Are you sure you want to initialized database'):
        Base.metadata.create_all(engine)
