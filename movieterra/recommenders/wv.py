from gensim.models import word2vec
import numpy as np
from movieterra.recommenders.helpers import movies_preproc, compute_tf, compute_idf

model = word2vec.Word2Vec.load('movieterra/recommenders/wv/keywords.model')

def form_kwords_sentences(input_movies):
    '''
        Helper function to find unknown words which are not in model.vocab
    '''
    unknown = []
    for index, kwords in enumerate(input_movies):
        for kword in kwords:
            if kword not in model.wv.vocab and kword != '':
                unknown.append(index)

    kwords_sentences = []
    for index in set(unknown):
        kwords_sentences.append(input_movies[index])
    return kwords_sentences

def check_kwords(input_kwords, premieres_kwords):
    '''
        Function to check if some of key words of movies are not in model vocab.
        If it finds such words, they will be added to the vocab 
        and model will be retrained in the context of all key words.
    '''
    kwords_sentences = []
    _vocab = model.wv.vocab
    kwords_sentences = form_kwords_sentences(input_kwords) + form_kwords_sentences(premieres_kwords)
    if kwords_sentences:
        model.build_vocab(kwords_sentences, update = True)
        model.save('movieterra/recommenders/wv/keywords.model')

def kwords2vec(kwords, all_input_kwords,logger):
    '''
        Evaluation of vector of the movie by averaging 
        all words vectors and multiplying it with TF-IDF score of word 
        in the corpus of all keywords
        
        input: kwords = ['love', 'spring']
        returns np.vector of shape 300
    '''
    tf_of_kwords = compute_tf(kwords)
    movie_vector = []
    for word in kwords:
        try:
            if all_input_kwords is not None:
                word_vector = model.wv.word_vec(word) * tf_of_kwords[word] * compute_idf(word, all_input_kwords)
            else:
                word_vector = model.wv.word_vec(word)
        except KeyError:
            logger.info('Keywords model passed the world on KW {}'.format(word))
            # print('Keywords model passed the world on KW {}'.format(word))
            continue
        movie_vector.append(word_vector) 
    movie_vector = np.array(movie_vector)
    return np.average(np.transpose(movie_vector), axis = 1)