import os
import sys
import traceback
import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from movieterra.common.utils import agent_premieres
from movieterra.workers.poster_image import *
from movieterra.workers.template import translator, months, VKINO_LOGIN, VKINO_PASSWORD,  MOVIE_METADATA_URL
POSTERS_FOLDER = 'movieterra/static' # !!!! абсолютный путь


def form_posters(agent_name, logger):
    if agent_name != 'vkino':
        return
    logger.info('Getting all movies from database..')
    actual_movies = [movie['agent_movie_id'] for movie in agent_premieres(agent_name)]    
    for movie in actual_movies:
        # print('-' * 110)
        logger.info('Trying to form poster for movie {}'.format(movie))
        filename = str(movie) + '_poster.png' 
        if filename in os.listdir('/home/movieterra/mvt/movieterra/static'):
            logger.info('Poster exists.')
            continue
        logger.info('Parsing data...')
        try:
            movie_response = requests.get(
                MOVIE_METADATA_URL.format(movie), 
                auth = HTTPBasicAuth(VKINO_LOGIN, VKINO_PASSWORD)
            )
            if movie_response.status_code == 200:
                logger.info('Status 200, parsing data...')
                movie_metadata_response = BeautifulSoup(movie_response.text, 'lxml')
            else:
                logger.info('Could not get movie. Vkino returned status {}'.format(movie_response.status_code), 'error')
        except Exception as e:
            error = traceback.format_exc().replace('\n', '')
            logger.error('Error in trying to parse base data: ')
            logger.error(error)
            logger.error(movie)
            logger.error('Continuing')
            continue
    
        try:
            logger.info('Parsing runtime...')
            runtime = movie_metadata_response.runningtime.text
            if runtime.translate(translator).isdigit():
                runtime = runtime.translate(translator)
                hours = round(int(runtime) / 60)
                minutes = round(int(runtime) / 60 - hours)
                if hours == 1:
                    fin = 'а'
                else:
                    fin = 'и'
                final_runtime = str(hours) + ' годин{} '.format(fin) + str(minutes) + ' хвилин'
            else:
                final_runtime = ''
        except Exception as e:
            logger.error('Error in parsing runtime')
            error = traceback.format_exc().replace('\n', '')
            logger.error(error)
            logger.error(movie)
        
        try:
            logger.info('Parsing relese date')
            releasedate = movie_metadata_response.releasedate.text 
            if releasedate != '':
                day = releasedate.split('-')[2][1] if releasedate.split('-')[2][0] == '0' else releasedate.split('-')[2]
                month = months[releasedate.split('-')[1]]
                releasedate_final = dict(day = day, month = month)
            else:
                releasedate_final = dict(day = '', month = '')
        except Exception as e:
            error = traceback.format_exc().replace('\n', '')
            logger.error(error)
            logger.error(movie)
            releasedate_final = dict(day = '', month = '')
        
        name = movie_metadata_response.namealt.text
    
        try:
            logger.info('Forming poster...')
            vkino_poster_url = movie_metadata_response.posterwide.url.text
            create_local_poster(vkino_poster_url, releasedate_final['month'], releasedate_final['day'], filename)      
        except Exception as e:
            logger.error('Error in forming poster: ')
            error = traceback.format_exc().replace('\n', '')
            logger.error(error)
            logger.error(movie)

if __name__ == '__main__':
    agent_name = sys.argv[1]
    form_posters(agent_name)
