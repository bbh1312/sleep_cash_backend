import os
from urllib.parse import quote_plus


class Config:
    DB_NAME = os.getenv('DB_NAME', 'sleep_cash')
    DB_USER = os.getenv('DB_USER', 'sleepcashuser')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'tmfflqzotl!@')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'change')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change2')
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')


class DevConfig(Config):
    DEBUG = True
