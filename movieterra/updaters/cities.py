import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from movieterra.updaters.utils import AGENTS_URL_DATA

login = AGENTS_URL_DATA['vkino']['auth']['login']
password = AGENTS_URL_DATA['vkino']['auth']['password']

cities_url = 'http://api.vkino.com.ua/catalog/cities/'
actual_url = 'http://api.vkino.com.ua/catalog/shows/actual.xml'
cities_soup = BeautifulSoup(requests.get(cities_url, auth = HTTPBasicAuth(login, password)).text, 'lxml')

cities_all_links = cities_soup.body.find_all('a')
cities = []
for link in cities_all_links :
    if link.text.split('/')[0].isdigit() or '..' in link.text or 'all' in link.text:
        continue
    else:
        cities.append(link.text.split('/')[0])    


soup = BeautifulSoup(requests.get(actual_url, auth = HTTPBasicAuth(login, password)).text, 'lxml')
actual_movies = [int(show.attrs['id']) for show in soup.shows.contents]
