''' все штуки которые связаны с парсингом и обновлением базы данных '''
import re

from datetime import datetime, timedelta

BOUNDS = [-3, 14] # 21

API_KEY = '00d5f265812d91c1267450ffc85e11f6' # for tmdb


BASE_PATH = 'https://api.themoviedb.org/3/movie/{}{}?api_key={}&language={}'
SEARCH_PATH = 'https://api.themoviedb.org/3/search/movie?query={}&api_key={}'
AGENTS_URL_DATA = {
    'planetakino' : {
        'url': 'http://planetakino.ua/api/movies',
        'auth': None,
        'path' : ['intheaters','soon'],
        'actual_indicator': 'has-showtimes'
        
    },
    'vkino' : {
        'url': 'http://api.vkino.com.ua/catalog/shows/actual.xml',
        'auth' : {
            'login': 'movieterra',
            'password' : 'OfzTMVT%'
        },
        'path': ['body', 'response', 'shows'],
        'actual_indicator' : None
    }
}

agents_cleaning_data = {
    'planetakino' : {
        'name_age_pattern' : '(\(\d{0,2}\+\))',
        'words_to_drop' : ['\(мовою оригіналу\)','\(кіномама\)','кіномама']
    },
    'vkino':{
        'words_to_drop' : ['\(британський театр в кіно\)','\(британський театр [в,у] кіно\)','\(фестиваль\)','\(сучасне кіно данії\)','\(кіноклуб без поп-корну\)','\(фестиваль американського кіно\)','\(мкф молодість 46\)',
                           '\(мовою оригіналу, без субтитрів\)','\(вихідні в опері\)','\(нове німецьке кіно\)','\(дні арабського кіно\)','\(фестиваль фільмів про кохання\)','\(мкф молодость 46\)',
                           '\(тиждень швейцарського кіно\)','\(тиждень італійського кіно\)','\(комеді франсез\)','\(переклад від ахтема редакторка ірин','\/ омкф','\(тиждень ізраїльського кіно\)',
                           '\(лат.полон\)', '\(кіностанція\)','\(родіна\)','\(кіно на десерт\)','\(тиждень іспанського кіно\)','\(фестиваль корейського кіно\)','\(опера та балет в кіно\)',
                           '\(британский театр в кино\)' ,'\(фільм-виставка\)', '\(фильм-выставка\)','\(мовою оригіналу\)','\(на языке оригинала\)', 'без попкорну','\(тиждень ізраїл кіно\)',
                           'без попкорна', 'кіно для батьків із малюками','кино для родителей с детьми', 'національний конкурс. частина \d{0,1}', 'национальный конкурс. часть \d{0,1}',\
                           '\(дні польського кіно\)','\(кіноклуб\)','\(опера і балет в кіно\)','\(фестиваль європейського кіно\)','\(мкф молодість 45\)','\(нове британське кіно\)',
                          '\(сучасне кіно угорщини\)','\(нове грузинске кіно\)','\(нове грузинське кіно\)','\(вечори французського кіно\)','\(вечори франц кіно\)','\(режисерська версія\)',
                           '\(еротичні короткометражки\)','\(міжнародний фестиваль фантастики\)','\(wajda week\)','\(американський фестиваль\)','\(балет\)','\(французька весна\)',
                           '\(лямур тужур\)','(тиждень австрійського кіно)','\(docudaysua\)','\(\)','\/ oiff','\(kisff 2017\)',
                           '\, part one: millenium approaches','\(єврейський кінофестиваль\)','\. частина 1','\. частина \d{0,2}','\(тиждень нідерландського кіно\)','#'
                          ],
        'name_age_pattern' :'\d{0,2}\+:'
    }
}

def preproc_movie_name(name, agent_name):
    name = re.sub(agents_cleaning_data[agent_name]['name_age_pattern'], '', name)
    for w in agents_cleaning_data[agent_name]['words_to_drop']:
        name = re.sub(w, '', name).strip().lower()
    return name


def in_bounds(release_date):
    if release_date:
        distance = (datetime.now() - release_date).days
        if BOUNDS[0] <= int(distance) and  int(distance) <= BOUNDS[1]:
            return True
        else: 
            return False
    return None
    #return BOUNDS[0] <= distance <= BOUNDS[1]
