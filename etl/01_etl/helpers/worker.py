from typing import Generator

from elasticsearch import Elasticsearch, helpers

from helpers.enums import Tables
from helpers.logger import LoggerFactory
from helpers.pg_connection_helpers import pg_cursor
from helpers.utils import coroutine, preprocess_rows
from settings import NUMBER_OF_FETCHED, STATE_KEY
from state.models import MovieRow, State

logger = LoggerFactory().get_logger()


class ETLWorker:

    def __init__(self, connection):
        self.connection = connection

    @coroutine
    def producer(self, next_node: Generator):
        while producer_args := (yield):
            last_modified, table = producer_args
            logger.info(f"Fetching changes from table {table}")
            sql = f'''
            SELECT id, modified
            FROM content.{table}
            WHERE modified > %s
            ORDER BY modified
            '''
            with pg_cursor(self.connection) as cursor:
                cursor.execute(sql, (last_modified,))
                while rows := cursor.fetchmany(NUMBER_OF_FETCHED):
                    next_node.send((table, rows))

    @coroutine
    def enricher(self, next_node: Generator, save_state: Generator):
        while enricher_args := (yield):
            table, rows = enricher_args
            last_modified = rows[-1]['modified']
            if table == Tables.FILM_WORK.value:
                save_state.send((table, last_modified))
                next_node.send((rows, last_modified))
            else:
                logger.info(f"Enriching changes from table {table}")
                sql = f'''
                SELECT fw.id, fw.modified
                FROM content.film_work fw
                LEFT JOIN content.{table}_film_work afw ON afw.film_work_id = fw.id
                WHERE afw.{table}_id IN %s
                ORDER BY fw.modified
                '''
                rows = preprocess_rows(rows)
                with pg_cursor(self.connection) as cursor:
                    cursor.execute(sql, (rows,))
                    while rows := cursor.fetchmany(NUMBER_OF_FETCHED):
                        save_state.send((table, last_modified))
                        next_node.send((rows, last_modified))

    @coroutine
    def merger(self, next_node: Generator):
        while merger_args := (yield):
            rows, last_modified = merger_args
            logger.info(f"Merging changes")
            sql_ = '''
            SELECT
                fw.id,
                fw.rating as imdb_rating,
                fw.title,
                fw.description,
                fw.type,
                COALESCE (
                   json_agg(
                       DISTINCT jsonb_build_object(
                           'id', g.id,
                           'name', g.name
                       )
                   ) FILTER (WHERE g.id is not null),
                   '[]'
                ) as genres,
                COALESCE (
                   json_agg(
                       DISTINCT jsonb_build_object(
                           'id', p.id,
                           'name', p.full_name
                       )
                   ) FILTER (WHERE p.id is not null AND pfw.role = 'director'),
                   '[]'
                ) as directors,
                COALESCE (
                   json_agg(
                       DISTINCT jsonb_build_object(
                           'id', p.id,
                           'name', p.full_name
                       )
                   ) FILTER (WHERE p.id is not null AND pfw.role = 'actor'),
                   '[]'
                ) as actors,
                COALESCE (
                   json_agg(
                       DISTINCT jsonb_build_object(
                           'id', p.id,
                           'name', p.full_name
                       )
                   ) FILTER (WHERE p.id is not null AND pfw.role = 'writer'),
                   '[]'
                ) as writers
            FROM
                content.film_work fw
            LEFT JOIN
                content.person_film_work pfw ON pfw.film_work_id = fw.id
            LEFT JOIN
                content.person p ON p.id = pfw.person_id
            LEFT JOIN
                content.genre_film_work gfw ON gfw.film_work_id = fw.id
            LEFT JOIN
                content.genre g ON g.id = gfw.genre_id
            WHERE
               fw.id IN %s
            GROUP BY
                fw.id;
            '''
            rows = preprocess_rows(rows)
            with pg_cursor(self.connection) as cursor:
                cursor.execute(sql_, (rows,))
                while rows := cursor.fetchmany(NUMBER_OF_FETCHED):
                    next_node.send((rows, last_modified))

    @coroutine
    def transform_movies(self, next_node: Generator):
        while transform_args := (yield):
            movie_dicts, last_modified = transform_args
            logger.info("Transforming movies from postgres")
            batch = []
            for movie_dict in movie_dicts:
                movie = MovieRow(**movie_dict)
                movie.transform()
                batch.append(movie)
            next_node.send((batch, last_modified))

    @coroutine
    def load_movies_to_elasticsearch(self, client: Elasticsearch, save_state_coro: Generator):
        while loader_args := (yield):
            movies: list[MovieRow]
            movies, last_modified = loader_args
            logger.info(f"Load {len(movies)} movies to ElasticSearch")
            data = [{
                "_index": "movies",
                "_id": row.id,
                "_source": {
                    "id": row.id,
                    "imdb_rating": row.imdb_rating,
                    "title": row.title,
                    "description": row.description,
                    "genre": row.genres_names,
                    "actors_names": row.actors_names,
                    "writers_names": row.writers_names,
                    "director": row.directors_names,
                    "actors": [dict(actor) for actor in row.actors],
                    "writers": [dict(writer) for writer in row.writers],
                }
            } for row in movies]
            _, errors = helpers.bulk(client, actions=data)
            save_state_coro.send(not errors)

    @coroutine
    def save_state_coro(self, state: State):
        while state_saver_args := (yield):
            key_to_save, last_modified_to_save = state_saver_args
            send_to_save = (yield)
            if send_to_save:
                logger.info(f"Las state: {STATE_KEY}: {state.get_state(STATE_KEY)}")
                state.set_state(f"{STATE_KEY}", last_modified_to_save)
