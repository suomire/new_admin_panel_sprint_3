from datetime import datetime
from time import sleep

import backoff
import elastic_transport
import psycopg2
from elasticsearch import Elasticsearch

from helpers.enums import Tables
from helpers.logger import LoggerFactory
from helpers.pg_connection_helpers import pg_connector
from helpers.utils import create_index_if_not_exists
from helpers.worker import ETLWorker
from settings import ELASTIC_CLIENT, INDEX_NAME, INDEX_PATH, PG_CONF, REFRESH_INTERVAL, STATE_KEY, \
    STATE_PATH
from state.json_file_storage import JsonFileStorage
from state.models import State

logger = LoggerFactory().get_logger()


@backoff.on_exception(backoff.constant, (psycopg2.OperationalError, elastic_transport.ConnectionError), max_tries=1000)
def start_etl_process():
    logger.info("Connecting to PostgreSQL")
    with pg_connector(PG_CONF) as conn:

        etl_worker = ETLWorker(conn)

        logger.info("Initiating coroutines")
        state_saver_ = etl_worker.save_state_coro(state)
        loader_ = etl_worker.load_movies_to_elasticsearch(es_client, state_saver_)
        transformer_ = etl_worker.transform_movies(next_node=loader_)
        merger_ = etl_worker.merger(next_node=transformer_)
        enricher_ = etl_worker.enricher(next_node=merger_, save_state=state_saver_)
        producer_ = etl_worker.producer(next_node=enricher_)

        while True:
            for table in Tables:
                logger.info('Starting ETL process for table %s', table.value)
                # sleep(5)
                producer_.send((state.get_state(STATE_KEY) or str(datetime.min), table.value))

            sleep(REFRESH_INTERVAL)


if __name__ == '__main__':
    logger.info("Initiating state")
    state = State(JsonFileStorage(STATE_PATH))
    sleep(10)
    es_client = Elasticsearch(ELASTIC_CLIENT['host'])
    logger.info(f"Create ES index if not exists")
    create_index_if_not_exists(es_client, index_path=INDEX_PATH, index_name=INDEX_NAME)

    start_etl_process()
