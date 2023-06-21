from enum import Enum


class Tables(Enum):
    FILM_WORK = "film_work"
    PERSON = "person"
    GENRE = "genre"


class FilworksTypes(Enum):
    TV_SHOW = "tv_show"
    MOVIE = "movie"
