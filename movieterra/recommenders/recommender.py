from datetime import datetime
from collections import Counter
from operator import itemgetter

from movieterra.models.agent import Agent
from movieterra.models.vkino import Vkino
from movieterra.models.recommendation import Recommendation
from movieterra.models.movie_recommendation import MovieRecommendation

from movieterra.recommenders.wv import check_kwords, kwords2vec
from movieterra.common.utils import flatten, table, get_user_movies, agent_tmdb_movies, agent_premieres
from movieterra.recommenders.helpers import movies_preproc, jaccard_similarity, get_movie_dict, genres2vec, get_similarities, get_weights


class Recommender:
    ''' 
        Class for creating recommendations for user.
        Recieves an orm-object of user and agent.
    '''
    def __init__(self, user, agent, logger):
        self.__user = user 
        self.__user_agent = agent 
        self.logger = logger

    def __cities_dates(self, premieres, agent_name):
        '''
            Cleaning premieres from those that are not in the city of user.
            Adding 2 parameters to each movie:
            1) 1 / number of cities where movie is actual
            2) number of days from release date
            input: premieres = [dict(tmdb_id, agent_movie_id),...]
            returns: premieres = [dict(tmdb_id, agent_movie_id, city, days),...]
        '''
        self.logger.debug('-before cleaning cities: '+str(len(premieres)))
        # self.logger.debug('why god why')
        actual_premieres = []
        self.logger.debug(str(premieres))
        for premiere in premieres:
            #self.logger.debug('please work '+str(premiere))
            movie = table[agent_name].query.filter_by(agent_movie_id = premiere['agent_movie_id']).first()
            if not movie.city:
                continue
            cities_of_movie = movie.city.split('|')
            cities_of_movie.remove('')
            
            self.logger.debug('--user cities: ' + str(self.__user.city))

            user_cities = dict(Counter(self.__user.city.split('|')))
            cities_items_list = list(user_cities.items())
            # если хоть какой-то город встречается больше 1го раза, 
            # то выбираем самый популярный из городов польз-ля
            if any(elem[1] > 1 for elem in cities_items_list): 
                user_cities = set([max(cities_items_list, key=itemgetter(1))[0]])
            else:
                user_cities = set(self.__user.city.split('|'))
            
            common = user_cities & set(cities_of_movie)
            self.logger.debug('--common: '+ str(common))

            # это не выбор самого популярного города            
            # common = set(self.__user.city.split('|')) & set(cities_of_movie)

            if common:
                premiere['city'] = 1 / len(cities_of_movie) /  len(premieres)*5
                distance = (datetime.now() - movie.release_date).days
                premiere['days'] = distance
                actual_premieres.append(premiere)
        self.logger.debug('-after cleaning from cities: '+str(len(actual_premieres)))
        return actual_premieres

    def __clear_previous_recs(self, premieres_matched): 
        '''
            Method for cleaning premieres from previous recommendations of user, which were delivered.
            premieres_matched: [dict(tmdb_id, agent_movie_id), ...]
        '''
        self.logger.debug('-before cleaning from previous recs: '+str(len(premieres_matched)))
        user_previous_recs = [rec.id for rec in Recommendation.query.filter_by(user_id = self.__user.id, delivered = 1).all()]
        user_previous_rec_movies = []
        for rec_id in user_previous_recs:
            ids_of_movies = [mv_rec.movie_id for mv_rec in MovieRecommendation.query.filter_by(recommendation_id = rec_id).all()]
            user_previous_rec_movies.append(ids_of_movies)
        user_previous_rec_movies = set(flatten(user_previous_rec_movies))   
        premieres_matched = [d for d in premieres_matched if d['agent_movie_id'] not in user_previous_rec_movies]
        self.logger.debug('-after cleaning from previous recs: '+str(len(premieres_matched)))
        return premieres_matched

    def __clear_premieres_from_input(self, premieres, user_tmdb_movies):
        ''' Method for cleaning premieres from input for not recommending 
            movies which are in user input
            premieres: [dict(tmdb_id, agent_movie_id), ...]
            actual_premieres: [dict(tmdb_id, agent_movie_id), ...]
        '''
        actual_premieres = []
        for premiere in premieres:
            if not (premiere['tmdb_id'] in user_tmdb_movies):
                actual_premieres.append(premiere)
        return actual_premieres

    def _collect_data(self, agent_name):
        '''
            Collecting data for input user movies and premieres of movies.
            Collecting premieres, than clean it from previous recs,
            clean from premieres which are not in user cities.
            --------------------------------------------------------------
            Vkino, PlanetaKino:
            Adding to premieres two new keys: city and days
            premieres = [dict(tmdb_id, agent_movie_id, city, days),...]

            Than it collects data for evaluating characteristics:
            kwords, genres, actors, directors.
            returns list of dicts.
        '''
        collected_input, collected_premieres = [], []
        user_tickets = get_user_movies(self.__user.id)
        user_tmdb_movies = agent_tmdb_movies(user_tickets, agent_name)
        self.logger.debug('User tmdb movies: ' + str(user_tmdb_movies))
        if user_tmdb_movies:
            premieres = agent_premieres(agent_name)
            premieres = self.__clear_premieres_from_input(premieres, user_tmdb_movies)
            if self.__user.id:
                # этот костыль был добавлен для того, чтобы не чистить рекомендации 
                # от прошлых рекомендаций (так надо)
                # для отмены расскоментировать 2 строки (121 и 122)
                self.logger.debug('Not gonna check previous recs !')
                # self.logger.debug('Checking previous recs...')
                # premieres = self.__clear_previous_recs(premieres) 
                self.logger.debug('go to the user city')
            if self.__user.city: 
                self.logger.debug('Checking user cities...')
                premieres = self.__cities_dates(premieres, agent_name) # город плюс кол-во дней от премьеры
                collected_premieres = list(map(lambda x: get_movie_dict(x['tmdb_id'], x['city'], x['days'], x['agent_movie_id']), premieres))
            else:
                collected_premieres = list(map(lambda x: get_movie_dict(x['tmdb_id'], agent_movie_id =  x['agent_movie_id'], city=None, days=None), premieres))
            
            collected_input = list(map(lambda x: get_movie_dict(x), user_tmdb_movies))
        return collected_input, collected_premieres

    def _form_features(self, collected_input, collected_premieres):
        '''
            Forming features for input movies and premieres.
            Genres: np.array of zero-one values with ones on the corresponding position:
                np.array([0,0,1,0,1,0...]) - shape of (18, 1)
            
            Key Words: np.array of float values of shape (300,1)
            
            Actor&Director weight: float value in the range (0,1) of jaccard_smilarities
                of input movie actors&directors and premieres.
            Novel weight: if author of premiere appears in authors of novel => +1
        '''

        collected_input = list(map(lambda x: movies_preproc(x), collected_input))
        collected_premieres = list(map(lambda x: movies_preproc(x), collected_premieres))

        check_kwords(collected_input, collected_premieres)
        input_actors = '|'.join(flatten([movie['actors'].split('|') for movie in collected_input]))
        input_authors = '|'.join(flatten([movie['novel'].split('|') for movie in collected_input]))
        input_directors = '|'.join(flatten([movie['director'].split('|') for movie in collected_input]))
        input_kwords = [movie['kwords'].split('|') for movie in collected_input]

        premieres_kwords = [movie['kwords'].split('|') for movie in collected_premieres]
        kw_context = flatten(input_kwords) + flatten(premieres_kwords)

        for movie in collected_input:
            movie['kwords_vector'] = kwords2vec(movie['kwords'].split('|'), kw_context, self.logger)
            movie['genres_vector'] = genres2vec(movie['genres'])
                 
        for movie in collected_premieres:
            movie['kwords_vector'] = kwords2vec(movie['kwords'].split('|'), None, self.logger)
            movie['genres_vector'] = genres2vec(movie['genres'])
            movie['actor_weight'] = jaccard_similarity(movie['actors'].split('|'), input_actors.split('|'))
            movie['director_weight'] = jaccard_similarity(movie['director'].split('|'), input_directors.split('|'))
            movie['author_weight'] = jaccard_similarity(movie['novel'].split('|'), input_authors.split('|'))

        return collected_input, collected_premieres
    
    def recommend(self):
        '''
            Forming top-similar array of movies in premieres to recommend to user by
            evaluating cosine-smilarities between keywords and genres vectors and adding actor/director
            weights.
        '''
        self.logger.info('*' * 100)
        self.logger.info('Script recommender started!')
        result = []
        collected_input, collected_premieres = self._collect_data(self.__user_agent.agent_name)
        self.logger.debug('Input: ' + str(len(collected_input)))
        self.logger.debug('Prmrs: ' + str(len(collected_premieres)))
        if collected_input:
            collected_input, collected_premieres = self._form_features(collected_input, collected_premieres)
            self.logger.debug('Getting similarities and weights...')
            collected_premieres = get_similarities(collected_input, collected_premieres)
            actor_weights = get_weights('actor_weight', collected_premieres)
            director_weights = get_weights('director_weight', collected_premieres)
            author_weights = get_weights('author_weight', collected_premieres)

            for movie, actor_weight, director_weight, author_weight in zip(collected_premieres, actor_weights, director_weights, author_weights):
                if round(movie['kw_sim']) == 0:
                    if 'city' in movie.keys() and movie['city']:
                        movie['relevance'] = movie['genres_sim'] + actor_weight + director_weight + movie['city'] + author_weight #+ movie['days']
                    else:
                        movie['relevance'] = movie['genres_sim'] + actor_weight + director_weight +author_weight
                if round(movie['genres_sim']) == 0:
                    if 'city' in movie.keys() and movie['city']:
                        movie['relevance'] = movie['kw_sim'] + actor_weight + director_weight + movie['city'] + author_weight#+ movie['days']
                    else:
                        movie['relevance'] = movie['kw_sim'] + actor_weight + director_weight + author_weight
                if round(movie['kw_sim']) != 0 and round(movie['genres_sim']) != 0:
                    if 'city' in movie.keys() and movie['city']:
                        movie['relevance'] = movie['kw_sim']*movie['genres_sim']+actor_weight+director_weight+movie['city'] + author_weight #+movie['days']
                    else: 
                        movie['relevance'] = movie['kw_sim']*movie['genres_sim']+actor_weight+director_weight + author_weight
                if  movie['kw_sim'] < 0 or movie['genres_sim'] < 0 or movie['relevance'] < 0.7:
                    continue
                else:
                    result.append(movie)
            result = list(reversed(sorted(result, key = lambda x: x['relevance'])))
            self.logger.debug('Result formed. {} from {}'.format(len(result), len(collected_premieres)))
        
        self.logger.info('Finished generating recommendations.')
        self.logger.info('*' * 100)
        return result
