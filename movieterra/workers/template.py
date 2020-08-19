import json 
import requests
import traceback
import os
import time

from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup  
from datetime import datetime
from jinja2 import Environment, FileSystemLoader 

from movieterra.common.utils import MOVIE_METADATA_URL, VKINO_LOGIN, VKINO_PASSWORD, TEMPLATES_PATH

translator = str.maketrans('', '', '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
TEMPLATE_NAME = 'vkino_template.html'
TEMPLATE_ENVIRONMENT = Environment(autoescape=False, loader=FileSystemLoader(TEMPLATES_PATH), trim_blocks=False)
ACCESS_KEY = 'FCRpHzn8PugrkdWEHStNQDZh'
max_plot_len = 314

SOURCE_URL = 'https://api.movieterra.com' #'http://127.0.0.1:5000' #'http://52.233.183.209:5000'# 'http://13.90.249.154'#'https://api.movieterra.com'
POSTERS_FOLDER = 'movieterra/static'

movie_dict_keys = ['name', 'nameorig', 'genres', 'runtime', 'country', 'actors', 'director',
                   'agelimit', 'plot', 'poster_url', 'poster_wide_url', 'movie_url', 'trailer_url']
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
months = {
    "01": "січня",
    "02": "лютого",
    "03": "березня",
    "04": "квітня",
    "05" : "травня",
    "06": "червня",
    "07":"липня",
    "08":"серпня",
    "09":"вересня",
    "10":"жовтня",
    "11":"листопада",
    "12": "грудня"   
}

def form_movie_dict(error_get_movie=False, **kwargs):
    ''' Просто вспомогательная функция для создания дикт для фильма'''
    movie_dict = dict()
    if error_get_movie:
        for key in movie_dict_keys:
            movie_dict[key] = 'null'
        return movie_dict
    for key, value in kwargs.items():
        movie_dict[key] = kwargs[key]
    return movie_dict

def render_template(context):
    return TEMPLATE_ENVIRONMENT.get_template(TEMPLATE_NAME).render(context)
 
def form_table_items(movies_to_recommend, logger = None):
    '''
        Функция, которая отвечает за формирование html-шаблона,
        Возвращает массив диктов (максимум 3 дикта для 3х фильмов),
        значения которых должны будут быть вставлены в html-шаблон с
        помощью функции render_template
    '''
    table_items = []
    for movie in movies_to_recommend:
        try:
            movie_response = requests.get(
                MOVIE_METADATA_URL.format(movie),
                auth=HTTPBasicAuth(VKINO_LOGIN, VKINO_PASSWORD)
            )
            print(movie_response.status_code)
            if movie_response.status_code == 200:
                movie_metadata_response = BeautifulSoup(movie_response.text, 'lxml')
            else:
                logger.debug('Could not get movie. Vkino returned status {}'.format(movie_response.status_code))
                context = dict(
                    table_items=[form_movie_dict(error_get_movie=True)])
                html = render_template(TEMPLATE_NAME, context)
                return dict(html = html, error = True)
        except Exception as e:
            error = traceback.format_exc().replace('\n', '')
            logger.debug(error)
            context = dict(table_items=[form_movie_dict(error_get_movie=True)])
            html = render_template(context)
            return dict(html = html, error = True)
            
        name = movie_metadata_response.namealt.text
        try:
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
            error = traceback.format_exc().replace('\n', '')
            logger.debug(error)
            final_runtime = None

        try:
            filename = str(movie) + '_poster.png'
            poster_url = '{}/{}/'.format(SOURCE_URL, 'static') + filename
            request_poster = requests.get(poster_url)
            if request_poster.status_code != 200:
                vkino_poster_url = movie_metadata_response.posterwide.url.text
                try:
                    releasedate = movie_metadata_response.releasedate.text
                    if releasedate != '' and releasedate is not None: 
                        day = releasedate.split('-')[2][1] if releasedate.split('-')[2][0] == '0' else releasedate.split('-')[2]
                        month = months[releasedate.split('-')[1]]
                        releasedate_final = dict(day=day, month=month)
                    else:
                        releasedate_final = dict(day='', month='')
                except Exception as e:
                    error = traceback.format_exc().replace('\n', '')
                    logger.error(error)
                    releasedate_final = dict(day='', month='')

                body = dict(
                        access_key = ACCESS_KEY, 
                        filename = filename, 
                        vkino_poster_url = vkino_poster_url,
                        month = releasedate_final['month'],
                        day = releasedate_final['day']
                    )
                resp = requests.post(SOURCE_URL + '/poster', data = json.dumps(body), headers=headers)
                if resp.status_code == 200:
                    final_poster_url = resp.text
                else:
                    final_poster_url = None
            else:
               final_poster_url = poster_url
            # final_poster_url = poster_url
        except Exception as e:
            error = traceback.format_exc().replace('\n', '')
            logger.error(error)
            final_poster_url = None

        if movie_metadata_response.plotalt.text is not None and movie_metadata_response.plotalt.text!='':
            plot = str(movie_metadata_response.plotalt.text)[:max_plot_len] + '...'
        else:
            plot = ''
        if movie_metadata_response.agelimit.text is not None:
            agelimit = str(movie_metadata_response.agelimit.text) + '+'
        else:
            agelimit = ''

        movie_dict = form_movie_dict(
                name=name,
                nameorig=movie_metadata_response.nameoriginal.text,
                genres=movie_metadata_response.genrealt.text,
                runtime=final_runtime,
                country=movie_metadata_response.countryalt.text,
                actors=movie_metadata_response.starringalt.text,
                director=movie_metadata_response.directoralt.text,
                agelimit=agelimit,
                plot=plot,  
                poster_url=movie_metadata_response.poster.url.text,
                poster_wide_url=final_poster_url,
                movie_url='https://vkino.ua/ua/show/{}'.format(
                    movie) + '#showtimes',
                trailer_url='https://vkino.ua/ua/show/{}'.format(
                    movie) + '?autoplay-video=on'
            )
        table_items.append(movie_dict)
    return table_items