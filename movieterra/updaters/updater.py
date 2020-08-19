import sys
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from movieterra.models import db
from movieterra.models.movie import Movie
from movieterra.models.vkino import Vkino
from movieterra.models.planetakino import PlanetaKino

from movieterra.updaters.utils import *
from movieterra.common.utils import flatten, table
from movieterra.updaters.tmdb import *
from movieterra.updaters.cities import cities, cities_url
from movieterra.updaters.posters import form_posters

def update_status(movies, agent_name, status):
    for movie in movies:
        m = table[agent_name].query.filter_by(agent_movie_id = movie).first()
        m.is_actual = status
        db.session.commit()
        print('Updated status to 0 for movie {}.'.format(movie))

def premiere_on_page(city, movie):
    '''
        Вспомогательный метод для проверки того, 
        есть ли показ фильма в данном городе прямо через сайт
    '''
    url = 'https://vkino.ua/ru/{}'
    soup = BeautifulSoup(requests.get(url.format(city)).text, 'lxml')
    premieres_box = soup.find('div', {'class':'film-box-holder'}).findAll('div','film-box')
    premieres_box_id = [int(m.find('a').attrs['href'].split('show/')[1].split('-')[0]) for m in premieres_box]
    return movie in premieres_box_id

def get_movie_cities(agent_movie_id, agent_name,auth, logger):
    '''
        Adding cities of movie (movie can be actual not in all cities.)
        Differs for agents.
        Vkino
        ---------------------------------
        Cities are being parsed in cities.py every time,
        a lot of cities. 
        
        парсим инфу о показах в городе, затем проверяем актуальность фильма
        и наличие его в показах этого города, затем
        смотрим чтобы хотя бы одна дата показа не была вчерашней
        (т.е. если в этом городе фильм актуален и если у него есть показы в будущем,
        то этот город можно добавить в города фильма)

        Planetakino
        ---------------------------------
        Has only 5 cities -  sumy|kharkov|lvov|odessa|kiev
        Принцип тот же, но есть костыль - для некоторых
        фильмов город нужно проверять 
        наличием показов в ссылке на этот фильм в данном городе,
        потому что раньше этот город не нашёлся
    '''
    actual_movies = premieres
    cities_of_movie = ''
    if auth: # vkino
        for city in cities:
            soup = BeautifulSoup(requests.get(cities_url + city + '/shows%2bshowtimes/', auth = HTTPBasicAuth(auth['login'], auth['password'])).text, 'lxml')
            showtimes_in_city = set()
            for l in soup.find_all('a'):
                item = l.text.split('.')[0].strip()
                if item != '' and item is not None:
                    showtimes_in_city.add(int(item))
            if agent_movie_id in showtimes_in_city and agent_movie_id in actual_movies:
                link = cities_url + city + '/shows%2bshowtimes/' + str(agent_movie_id) +'.xml'
                showtime_city_dates =  BeautifulSoup(requests.get(link, auth = HTTPBasicAuth(auth['login'], auth['password'])).text, 'lxml')
                dist = []
                for date in showtime_city_dates.dates.contents:
                    distance = (datetime.now() - datetime.strptime(date.text, '%Y-%m-%d')).days
                    dist.append(distance)
                if any(d <= 0 for d in dist) and premiere_on_page(city, agent_movie_id):
                    cities_of_movie += city + '|'
    else:
        url = 'https://planetakino.ua/' #'https://planetakino.ua/{}/movies'
        for city in 'sumy|kharkov|lvov|odessa|kiev'.split('|'):
            movies_in_city = []
            soup = BeautifulSoup(requests.get(url + city).text, 'lxml')
            movies_list = soup.findAll("div", {"class": "movies-list"}) # now and soon content__section
            for ls in movies_list:
                # это просто все возможные показы в этом городе
                # проверка их наличия в премьерес и подходимости по дате
                movies_in_city+=list(map(lambda x: int(x.attrs['data-filmid']), ls.findAll("div", {"class": "movie-block__info-icon-wishlist"})))
            if agent_movie_id in movies_in_city and agent_movie_id in premieres: #and city_in_bounds(city, agent_movie_id):
                # print('подходит')
                cities_of_movie+=city+'|'
           
        
        if cities_of_movie == '':
            # print('ВСЁ ЕЩЁ НЕ НАШЛИ ГОРОД ДЛЯ ФИЛЬМА', agent_movie_id)
            # взять из апи ссылку на фильм и пробежаться по ней вставляя города
            r = BeautifulSoup(requests.get('https://planetakino.ua/api/movies').text, 'lxml')
            tag = [tag for tag in r.findAll('id') if tag.text == str(agent_movie_id)][0]
            link = tag.parent.movielink.text
            for city in 'sumy|kharkov|lvov|odessa|kiev'.split('|'):
                link2 = link.split('movies')[0] + city + '/movies' + link.split('movies')[1]
                req = requests.get(link2)
                if req.status_code == 200:
                    soup = BeautifulSoup(req.text, 'lxml')
                    showtime_container = soup.find('div', {"class": "showtime-movie-container"})
                    if showtime_container:
                        if not showtime_container.find('div', {"class":"showtimes-row"}).find('span', {"class":"past"}):
                            cities_of_movie+=city+'|'
    
    logger.info('--cities of movie: ' + str(cities_of_movie))
    return  cities_of_movie

def write_in_db(data, agent_name,logger):
    ''' Insert/Update movie in db with all parsed characteristics '''
    def update_agent_row(agent_movie_data, agent_name):
        agent_movie = table[agent_name].query.filter_by(agent_movie_id = agent_movie_data['agent_movie_id']).first()
        for key, value in agent_movie_data.items():
            if value:
                agent_movie.__setattr__(key, value)
                db.session.commit()
        # print('Updated row for movie {}, {}'.format(agent_movie.name, agent_movie.agent_movie_id))
        return agent_movie
    def insert_agent_row(agent_movie_data, agent_name):
        new_agent_movie = table[agent_name](
                agent_movie_id=agent_movie_data['agent_movie_id'],
                is_premiere=agent_movie_data['is_premiere'],
                release_date=agent_movie_data['release_date'],
                year=agent_movie_data['year'],
                name=agent_movie_data['name'],
                nameoriginal=agent_movie_data['nameoriginal'],
                dates=agent_movie_data['dates'],
                city=agent_movie_data['city'],
                is_actual=agent_movie_data['is_actual']
            )
        db.session.add(new_agent_movie)
        db.session.commit()
        # print('Inserted row movie {} to db with additional data.'.format(new_agent_movie.agent_movie_id))
        return new_agent_movie

    agent_movies = []
    for agent_movie_data in data: # movie is dict
        if not table[agent_name].query.filter_by(agent_movie_id = agent_movie_data['agent_movie_id']).first():
            movie_orm_object = insert_agent_row(agent_movie_data, agent_name)
            if logger:
                logger.info('-inserted movie {}'.format(movie_orm_object.name))
        else:
            movie_orm_object = update_agent_row(agent_movie_data, agent_name)
            if logger:
                logger.info('-updated movie {}'.format(movie_orm_object.name))
        agent_movies.append(movie_orm_object)
    if logger: 
        logger.info('-created/updated such amount of movies: {}'.format(len(agent_movies)))
    return agent_movies

def set_tmdb_for_actual(actual_movies, agent_name,logger):
    '''
        Search for premiere movie in tmdb,
        cleaning search results, and juxtapose 
        agent_movie_id with tmdb_id
    '''
    for agent_movie in actual_movies:
        if agent_movie.tmdb_fk_id:
            continue
        query = [agent_movie.name, agent_movie.nameoriginal]
        search_results = search(query) # получили всё шо нашлось на английском и на укр # это массив [[ukr], [eng]]
        tmdb_id = match(search_results, agent_movie, agent_name) # здесь находим правильное совпадение [movie, tmdb_id]
        if tmdb_id:
            tmdb_movie = Movie.query.filter_by(tmdb_id = tmdb_id).first()
            if not tmdb_movie:
                new_movie_data = collect_info(tmdb_id)
                new_movie = Movie(datetime.now(), datetime.now(), tmdb_id, new_movie_data['poster_path'], new_movie_data['director'],new_movie_data['novel'], new_movie_data['actors'],new_movie_data['budget'],new_movie_data['genres'],new_movie_data['kwords'],new_movie_data['runtime'],new_movie_data['title'])
                db.session.add(new_movie)
                db.session.commit()
        agent_movie.tmdb_fk_id = tmdb_id 
        db.session.commit()     

def filter_data_by_dates_and_parse(soup,agent_name, auth, logger):
    '''
        Filter all new parsed actual movies and parsing additional
        info about those which are in bounds(-14,+3 days)
    '''
    
    actual_showtimes = []
    if auth:
        shows = soup.shows.contents
    else:
        shows = soup.intheaters.contents + soup.soon.contents
        shows = [show for show in shows if show.find('has-showtimes')]
    
    logger.info('-searching in all showtimes...')

    for show in shows:
        if (show.find('releasedate') and show.releasedate.text):
            release_date = datetime.strptime(show.releasedate.text, '%Y-%m-%d')  
        elif (show.find('sincedate') and show.sincedate.text):
            release_date = datetime.strptime(show.sincedate.text, '%Y-%m-%d')
        
        if in_bounds(release_date):
            agent_movie_data = dict()
            agent_movie_data['is_actual'] = 1
            agent_movie_data['release_date'] = release_date
            agent_movie_data['agent_movie_id'] = int(show.id.text) if show.find('id') else int(show.attrs['id'])
            

            if auth: # vkino
                agent_movie_data['name'] = preproc_movie_name(show.namealt.text, agent_name)  
                agent_movie_data['is_premiere'] = 1 if (show.ispremiere and show.ispremiere.text == 'y') else 0
                agent_movie_data['year'] = int(show.year.text) if show.year.text else None
                dates_ = soup.find('dates')
                agent_movie_data['dates'] = ''.join([d.text + '|' for d in dates_.contents]) if dates_.contents else None
            else: # planetakino
                agent_movie_data['name'] = preproc_movie_name(show.find('name').text, agent_name)
                agent_movie_data['is_premiere'] = 1 if show in soup.soon.contents else 0
                agent_movie_data['year'] = int(show.sincedate.text.split('-')[0]) if show.sincedate.text else None
                numdays = (datetime.strptime(show.enddate.text, '%Y-%m-%d') - agent_movie_data['release_date']).days
                dates_ = '|'.join([str(agent_movie_data['release_date'] + timedelta(days=x))[:10] for x in range(0, numdays+1)])
                agent_movie_data['dates'] = dates_
            

            logger.info('-movie {} in dounds by dates. '.format(agent_movie_data['name']))

            agent_movie_data['nameoriginal'] = preproc_movie_name(show.nameoriginal.text, agent_name)
            logger.info('-starting parse cities...')
            agent_movie_data['city'] = get_movie_cities(agent_movie_data['agent_movie_id'], agent_name, auth, logger) 
            actual_showtimes.append(agent_movie_data)

    return actual_showtimes

def check_for_updates(agent_name, logger=None):
    '''
        Checking all movies with is_actual = 1 in db for relevance.
        (Relevance means: release_date of movie is in bounds (-14,+3 days) and it is in
        actual movies of agent API.)

        If some new movies were added, parsing all info about them,
        inserting in db and finding a tmdb_id of this movie.
    '''
    # THIS IS DEBUG ONLY
    if logger is None:
        import logging
        logging.basicConfig(
            level = logging.DEBUG,
            format="%(asctime)s [%(levelname)s]: %(message)s",
            datefmt = '%d/%m/%Y %H:%M:%S',
            # если раскоментировать то не будет выводиться на консоль
        #    filename = 'movieterra/log/app.log'
        )
        logger = logging.getLogger(__name__)
    # Всё уже не дебаг

    logger.info('#' * 100)
    logger.info('Updater started')
    logger.info('Checking {} NOW.'.format(agent_name))
    
    global premieres

    _actual_showtimes = table[agent_name].query.filter_by(is_actual = 1).all()
    for m in _actual_showtimes:
        if not in_bounds(m.release_date):
            m.is_actual = 0
            db.session.commit()

    current_actual = set([movie.agent_movie_id for movie in _actual_showtimes])
    
    logger.info('Current amount in actual: {}'.format(len(current_actual)))

    movies_url = AGENTS_URL_DATA[agent_name]['url']
    auth = AGENTS_URL_DATA[agent_name]['auth']
    actual_indicator = AGENTS_URL_DATA[agent_name]['actual_indicator']
    if auth:
        soup = BeautifulSoup(requests.get(movies_url, auth = HTTPBasicAuth(auth['login'], auth['password'])).text, 'lxml')
        premieres = set([int(premiere.attrs['id']) for premiere in soup.shows.contents])
    else:
        soup = BeautifulSoup(requests.get(movies_url).text, 'lxml')
        premieres = soup.intheaters.contents + soup.soon.contents   
        premieres = set([int(premiere.id.text) for premiere in premieres if premiere.find(AGENTS_URL_DATA[agent_name]['actual_indicator'])])
    
    logger.info('Current amount of premier: {}'.format(len(premieres)))

    if len(current_actual - premieres) > 0:
        removed = current_actual - premieres
        logger.info('There were removed {} movies'.format(len(removed)))
        update_status(removed, agent_name, 0)

    if len(premieres - current_actual) > 0:
        added = premieres - current_actual
        logger.info('There were added {} movies to premieres'.format(len(added)))
        logger.info('Starting filter movies by dates and parse movie data...')
        actual_showtimes = filter_data_by_dates_and_parse(soup, agent_name, auth, logger) 
        logger.info('Writing to the db...')
        actual_agent_movies = write_in_db(actual_showtimes, agent_name, logger)     
        logger.info('Searching tmdb_id for actual movies... ')
        set_tmdb_for_actual(actual_agent_movies, agent_name, logger)         
        logger.info('Posters...')
        form_posters(agent_name,logger)


    if len(current_actual - premieres) == 0:
        logger.info('No changes.')

if __name__ == '__main__':
    print('Script started for updating {}'.format(sys.argv[1]))
    check_for_updates(sys.argv[1])