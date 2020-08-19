from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from movieterra.models.movie import Movie

all_genres = np.array(['action', 'adventure', 'animation', 'comedy', 'crime', 'documentary', 'drama', 'family','fantasy', 'history', 'horror', 'music', 'mystery','romance', 'science fiction', 'thriller', 'war', 'western'])
sw = set(stopwords.words('english'))


def lowercase(x):
    ''' Helper function to lowercase key words. '''
    if str(x) != 'nan' and x is not None:
        return x.lower()

def tokenization(kw_string):
    ''' Helper function to tokenize key words. '''
    if isinstance(kw_string, float) or kw_string is None: 
        return None
    new_str = ''
    for s in kw_string.split('|'):
        arr = [w for w in word_tokenize(s) if w not in sw and w != '\'' and w != '\'s']
        for word in arr:
            new_str += word
            new_str += '|'
    kw_list = new_str.split('|')
    kw_list.remove('')
    return '|'.join(kw_list) 

def movies_preproc(movie):
    ''' Preprocessing: tokenization and lowercasing. '''
    movie['kwords'] = tokenization(lowercase(movie['kwords']))
    movie['genres'] = lowercase(movie['genres'])
    movie['actors'] = lowercase(movie['actors'])
    movie['director'] = lowercase(movie['director'])
    return movie

def compute_tf(kwords):
    '''
        Computing of term-frequency of key word in the contex of all key words 
        from premieres and user movies.
    '''
    tf_text = Counter(kwords)
    for key in tf_text:
        tf_text[key] = tf_text[key]/float(len(kwords))
    return dict(tf_text)

def compute_idf(word, corpus):
    '''
        Computing of inverse-document-frequency of key word in the contex of all key words 
        from premieres and user movies.
    '''
    return np.log10(len(corpus)/sum([1 for i in corpus if word in i])) 

def jaccard_similarity(query, document):
    '''
        Jaccard similarity metric for evaluating weights of directors/actors for movies.
    '''
    intersection = set(query).intersection(set(document))
    union = set(query).union(set(document))
    return len(intersection)/len(union)

def get_movie_dict(tmdb_id, city = None, days = None, agent_movie_id = None):
    '''
        Helper function to get movie features from database.
    '''
    movie = Movie.query.filter_by(tmdb_id = tmdb_id).first()
    if movie:
        # if not city:
            # m = dict(kwords = movie.kwords, genres = movie.genres, actors = movie.actors, director = movie.director, tmdb_id = tmdb_id)
        # else:
        m = dict(
            kwords = movie.kwords, 
            genres = movie.genres, 
            actors = movie.actors, 
            director = movie.director, 
            novel = movie.novel,
            tmdb_id = tmdb_id,
            city = city,
            days = days,
            agent_movie_id = agent_movie_id
            )
    else:
        m = None
    return m

def genres2vec(input_genres):
    '''
        Function to form and return a  binary np.array with ones 
        on the corresponding value of genre in all_genres.
    '''
    genres_vector = np.zeros(len(all_genres))
    for genre in all_genres:
        for input_genre in input_genres.split('|'):
            if input_genre in all_genres:
                genres_vector[np.where(all_genres == input_genre)[0][0]] = 1
    return genres_vector

def get_similarities(collected_input, collected_premieres):
    '''
        Helper function to evaluate cosine similarities between user input movies and movies in premieres.
        (Uses genres and key words vector of movie)
    '''
    user_kw_vector = np.average(np.transpose(np.array([movie['kwords_vector'] for movie in collected_input])), axis = 1)
    user_genres_vector = np.average(np.transpose(np.array([movie['genres_vector'] for movie in collected_input])), axis = 1)

    for movie in collected_premieres:
        kw_sim = cosine_similarity(user_kw_vector.reshape(1, -1), movie['kwords_vector'].reshape(1, -1))
        genres_sim = cosine_similarity(user_genres_vector.reshape(1, -1), movie['genres_vector'].reshape(1, -1))
        movie['kw_sim'] = kw_sim[0][0]
        movie['genres_sim'] = genres_sim[0][0]

    return collected_premieres

def get_weights(key, collected_premieres):
    ''' Helper function '''
    weights = [r[key] for r in collected_premieres]
    return weights