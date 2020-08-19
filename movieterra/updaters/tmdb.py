import requests

from movieterra.updaters.utils import *


TMDB_TIME_LIMIT = 10 # 40 requests every 10 seconds
NUM_OF_PEOPLE = 5

def match(results, movie, agent_name):
    '''
        самая трешовая функция. чистит результаты поисковых запросов с тмдб
        (чтобы поставить в соответствие именно тот фильм)
        чаще всего всё находится по украинсокому названию, но не всегда
        для этого проверяются английские название и год (если есть)
    '''
    if not results[0] and not results[1]:
        print('No info about movie {}, {}. Tmdb_id will be null.'.format(movie.agent_movie_id, movie.name))
        return 
    elif len(results[0]) == 1: # если нашлось на украинском то это то шо надо
        return results[0][0]['id']
    elif len(results[0]) > 1 and len(results[1]) != 0:
        ukr_index = [item['id'] for item in results[0]]
        en_index = [item['id'] for item in results[1]]
        common = list(set(ukr_index) & set(en_index))
        if len(common) == 1:
            return common[0]
        else:
            main_results_by_date = [elem for elem in results[0] if elem['id'] in common]
            if movie.year:
                main_results_by_date = [result for result in results[0] if result['release_date'].split('-')[0] and (int(result['release_date'].split('-')[0]) == movie.year or int(result['release_date'].split('-')[0]) == movie.year - 1 or int(result['release_date'].split('-')[0]) == movie.year + 1)]

            if len(main_results_by_date) == 1:
                return main_results_by_date[0]['id']
            try:
                main_results_by_date = list(sorted(main_results_by_date, key = lambda x: x['release_date'], reverse = True))[0]
                id = main_results_by_date['id']
                return id
            except:
                pass # оно должно найтись дальше
    elif len(results[0]) == 0:
        if len(results[1]) == 1:
            return results[1][0]['id']
        else:
            if movie.year and int(movie.year) > 1975: # просто потому что
                en_results_by_date = [result for result in results[1] if result['release_date'].split('-')[0] and (int(result['release_date'].split('-')[0]) == movie.year or int(result['release_date'].split('-')[0]) == movie.year - 1 or int(result['release_date'].split('-')[0]) == movie.year + 1)]
                if len(en_results_by_date) == 1:
                    return en_results_by_date[0]['id']
                else:
                    for m in en_results_by_date:
                        if len(m['original_title'].lower()) == len(movie.nameoriginal):
                            return en_results_by_date[0]['id']
                        else:
                            en_results_by_date = list(sorted(results[1], key = lambda x: x['release_date'], reverse = True))[0]
                            id = en_results_by_date['id']
                            return id
    elif len(results[1]) == 0:
        if len(results[0]) == 1:
            return results[0][0]['id']
        else:
            if movie.year and int(movie.year) > 1975: # ?????
                main_results_by_date = [result for result in results[0] if result['release_date'].split('-')[0] and (int(result['release_date'].split('-')[0]) == movie.year or int(result['release_date'].split('-')[0]) == movie.year - 1 or int(result['release_date'].split('-')[0]) == movie.year + 1)]
                if len(main_results_by_date) == 1:
                    return main_results_by_date[0]['id']
                else:
                    for m in main_results_by_date:
                        if len(m['original_title'].lower()) == len(orig_title):
                            return  m['id']
                        else:
                            main_results_by_date = list(sorted(results[0], key = lambda x: x['release_date'], reverse = True))[0]
                            id = main_results_by_date['id']
                            return  id
            else:
                return

def search(queries):
    '''queries = [query_ukr, query_en]'''
    results = [] #, limit = [], 0
    for query in queries:
        result = []
        if query: # ???
            response = requests.get(SEARCH_PATH.format(query, API_KEY))
            if response.status_code == 200:
                result = response.json()['results']
                limit = int(response.headers['X-RateLimit-Remaining']) 
        results.append(result)
    return results #, limit # всё шо нашлось на украинском и всё шо нашлось на английском + сколько запросов нам ещё можно делать

def get(method, language = 'en', special_details = ''):
    link = BASE_PATH.format(method, special_details, API_KEY, language)
    r = requests.get(url = link)
    return r.json(), int(r.headers['X-RateLimit-Remaining'])

def collect_info(tmdb_id):
    ''' Collecting data about premiere movie on tmdb by tmdb_id 
        (title, poster, budget, runtime, genres, keywords, director, novel author, actors)
    '''
    title, limit = get(str(tmdb_id), language = 'ru')
    # if 'status_code' in title and title['status_code'] == 34:
    
    title = title['title']
    
    response, limit = get(str(tmdb_id)) # info
    
    poster_path = response['poster_path']
    budget = response['budget']
    runtime = response['runtime']
    genres = '|'.join([genre['name'] for genre in response['genres']]).lower()
        
    kwords, limit = get(str(tmdb_id), special_details = '/keywords')
    kwords = '|'.join([kword['name'] for kword in kwords['keywords']]).lower()
    
    
    credits, limit = get(str(tmdb_id), special_details = '/credits')
    director = '|'.join([item['name'] for item in credits['crew'] if item['job'] == 'Director'][:NUM_OF_PEOPLE])
    novel = '|'.join([item['name'] for item in credits['crew'] if item['job'] == 'Novel'][:NUM_OF_PEOPLE])
    actors = '|'.join([item['name'] for item in credits['cast']][:NUM_OF_PEOPLE])
    
    result = dict(
        poster_path = poster_path,
        director = director,
        novel = novel,
        actors = actors,
        budget = budget,
        runtime = runtime,
        genres = genres,
        kwords = kwords,
        title = title
    )    
    return result

