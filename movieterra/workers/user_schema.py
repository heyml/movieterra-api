from datetime import datetime

from movieterra.common.utils import table

from movieterra.models import db
from movieterra.models.user import User
from movieterra.models.ticket import Ticket
from movieterra.models.recommendation import Recommendation
from movieterra.models.movie_recommendation import MovieRecommendation
from movieterra.models.vkino import Vkino

def add_tickets(user_id, movies_to_add, logger):
    for movie in movies_to_add:
        ticket = Ticket(user_id, movie, datetime.now(), datetime.now())
        logger.debug('Ticket {} for user {} was added'.format(movie, user_id))
        db.session.add(ticket)
        db.session.commit()

def update_user_row(data, user, logger):
    logger.debug('Updating user data...')
    prev_user_movies = Ticket.query.filter_by(user_id = user.id).all()
    if prev_user_movies: 
        if type(data.get('movies')) is str:
            movies_to_add = set([int(movie) for movie in data.get('movies').split('|')])
        else:
            movies_to_add =  set([int(movie) for movie in data.get('movies')])
    movies_to_add = movies_to_add - set([ticket.movie_id for ticket in prev_user_movies])
    if movies_to_add:
        add_tickets(user.id, movies_to_add, logger)
        logger.debug('Added all tickets for user {}'.format(user.id))
    else:
        logger.debug('All tickets already in db for user {}'.format(user.id))

    if user.city and data.get('city') and  user.city != data.get('city'):
        if type(data.get('city')) is str:
            cities_data = set(data.get('city').strip().split('|')) if '|' in data.get('city') else data.get('city').strip()
        else:
            cities_data = set(data.get('city'))
        new_cities = set(cities_data) - set(user.city.strip().split('|'))
        # new_cities = set(data.get('city').strip().split('|')) - set(user.city.strip().split('|'))
        if new_cities:
            new_cities = '|'.join(new_cities)
            user.city = user.city.strip() + '|' + new_cities
            user.updated_at = datetime.now()
            db.session.commit()
            logger.debug('Updated city status for user {}'.format(user.id))
    if data.get('email') and user.email != data.get('email'):
        user.email = data.get('email')
        db.session.commit()
        logger.debug('Updated E-MAIL for user {}'.format(user.id))
    return 'User updated.\n' # можно ничего не возвращать

def insert_user_row(data, agent, logger):
    logger.info('Inserting user data...')
    if type(data.get('city')) is list:
         cities_data = '|'.join(data.get('city'))
    if type(data.get('city')) is str:
        logger.debug('!!!!!it is str')
        cities_data = data.get('city').strip()

    user = User(datetime.now(), datetime.now(), data.get('user_id'), agent.id, data.get('username'), data.get('email'), cities_data)
    db.session.add(user)
    db.session.commit()
    logger.debug('Added user {}'.format(user.id))
    if type(data.get('movies')) is str:
        movies_to_add = [int(movie) for movie in data.get('movies').split('|')]
    else:
        movies_to_add =  [int(movie) for movie in data.get('movies')]
    add_tickets(user.id, movies_to_add, logger) 
    logger.debug('Added all tickets for user {}'.format(user.id))
    db.session.commit()
    return 'User created.\n' # тут можно ничё не возвращать

def insert_recommendation_row(user, agent, result, logger = None):
    r = Recommendation(user.id, agent.id, datetime.now())
    db.session.add(r)
    db.session.commit()
    if logger: logger.debug('Added recommendations to db')
    for movie in result:
        mr = MovieRecommendation(r.id, movie, datetime.now())
        db.session.add(mr)
        db.session.commit()
    return r.id

def sort_by_dates(recommendations, agent_name):
    result_dates = []
    for movie in recommendations:
        agent_movie = table[agent_name].query.filter_by(agent_movie_id = movie).first()
        result_dates.append([movie, agent_movie.release_date])
    result_dates = list(reversed(sorted(result_dates, key = lambda x: x[1])))
    result_dates = [el[0] for el in result_dates] 
    return result_dates