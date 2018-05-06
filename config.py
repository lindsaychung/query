import os

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:ilovehifi@localhost/hifitrackD72?charset=utf8'

