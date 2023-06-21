import os

from dotenv import load_dotenv

load_dotenv()

REFRESH_INTERVAL = 10
LOGGER_PATH = "logger.conf"

PG_CONF = {
    'dbname': os.environ.get('PG_DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': os.environ.get('DB_PORT', 5432)
}

ELASTIC_CLIENT = {
    'host': f'http://{os.environ.get("ELASTIC_HOST")}:{os.environ.get("ELASTIC_POST")}'
}

STATE_KEY = 'last_movies_updated'
STATE_PATH = 'storage.json'

NUMBER_OF_FETCHED = 100

INDEX_PATH = "helpers/index.json"
INDEX_NAME = "movies"
