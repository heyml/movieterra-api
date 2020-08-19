import csv
from movieterra.updaters.updater import write_in_db, set_tmdb_for_actual

fields = ['agent_movie_id','tmdb_fk_id','is_actual','release_date','year','nameoriginal','dates','is_premiere','city','name']

with open('sample.csv', 'r') as file:
	movies = list(csv.reader(file))

print(movies)

data = []

for movie in movies:
	movie_dict = dict()
	for f in fields:
		movie_dict[f] = None
	movie_dict['agent_movie_id'] = int(movie[0])
	movie_dict['name'] = movie[1].strip()
	movie_dict['nameoriginal'] = movie[2].strip()
	data.append(movie_dict)

agent_movies = write_in_db(data, 'planetakino', None)
print('фильмы записаны в бд')
set_tmdb_for_actual(agent_movies, 'planetakino', None) 
print('для всех найдены соответствия')
