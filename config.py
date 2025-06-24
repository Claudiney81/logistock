import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = 'sua-chave-secreta-segura'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'logistock.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
