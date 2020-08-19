from movieterra.models.vkino import Vkino
from movieterra.models.ticket import Ticket
from movieterra.models.planetakino import PlanetaKino

table = {'vkino': Vkino, 'planetakino': PlanetaKino}

flatten = lambda l: [item for sublist in l for item in sublist]

VKINO_LOGIN = 'movieterra'
VKINO_PASSWORD = 'OfzTMVT%'
TEMPLATES_PATH = 'movieterra/templates'
MOVIE_METADATA_URL = 'http://api.vkino.com.ua/catalog-cinema/shows/{}.xml' 

def get_user_movies(user_id): 
    '''Returns array of agent_movie_id elements of user'''
    tickets = Ticket.query.filter_by(user_id = user_id).all()
    user_movies = [ticket.movie_id for ticket in tickets]
    return user_movies

def agent_tmdb_movies(user_movies, agent_name):
    '''Array of tmedb_id of movies of user'''
    user_tmdb_movies = []
    for movie in user_movies:
        tmdbid = table[agent_name].query.filter_by(agent_movie_id = movie).first()
        if tmdbid is not None and tmdbid.tmdb_fk_id:
            user_tmdb_movies.append(tmdbid.tmdb_fk_id)
    return user_tmdb_movies

def agent_premieres(agent_name):
    '''Returns all actual premieres in all cities with existing tmdb_id of movies'''
    premieres = [dict(tmdb_id=movie.tmdb_fk_id, agent_movie_id=movie.agent_movie_id) for movie in table[agent_name].query.filter(table[agent_name].tmdb_fk_id != None , table[agent_name].is_actual == 1).all()]
    return premieres


# def vkino_tmdb_movies(user_movies):
#     user_tmdb_movies = []
#     for movie in user_movies:
#         tmdbid = Vkino.query.filter_by(agent_movie_id = movie).first()
#         if tmdbid is not None and tmdbid.tmdb_fk_id:
#             user_tmdb_movies.append(tmdbid.tmdb_fk_id)
#     return user_tmdb_movies

# def pk_tmdb_movies(user_movies):
#     user_tmdb_movies = []
#     for movie in user_movies:
#         tmdbid = PlanetaKino.query.filter_by(agent_movie_id = movie).first()
#         if tmdbid is not None and tmdbid.tmdb_fk_id:
#             user_tmdb_movies.append(tmdbid.tmdb_fk_id)
#     return user_tmdb_movies

# def vkino_premieres():
#     premieres = [dict(tmdb_id=movie.tmdb_fk_id, agent_id=movie.agent_movie_id) for movie in Vkino.query.filter(Vkino.tmdb_fk_id != None , Vkino.is_actual == 1).all()]
#     return premieres

# def pk_premieres():
#     premieres = [dict(tmdb_id=movie.tmdb_fk_id, agent_id=movie.agent_movie_id) for movie in PlanetaKino.query.filter(PlanetaKino.tmdb_fk_id != None , PlanetaKino.is_actual == 1).all()]
#     return premieres