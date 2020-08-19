import requests  
import json 
import traceback  
import csv 
import os  
from requests.auth import HTTPBasicAuth 
import argparse  
import re
from time import strftime 


parser = argparse.ArgumentParser(description='Parse input string')
parser.add_argument('string', help='Input filename or filepath', nargs='+')
args = parser.parse_args()
FILE_NAME = args.string[0]

ESPUTNIK_USER = 'hello@mynameisjura.com' 
ESPUTNIK_PASSWORD = 'MovieterraHeyML2017'
SUBJECT = 'Вам сподобається: рекомендаційна система Вкіно радить подивитися'
PLAIN_TEXT = ' Рекомендовані вам фільми обрані штучним інтелектом на основі ваших попередніх покупок квитків онлайн. Ви отримали'

SOURCE_URL = 'https://api.movieterra.com'
POSTERS_FOLDER = 'static'
TEMPLATES_PATH = 'templates'

HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}
EMAIL_API_METHOD = 'https://esputnik.com/api/v1/message/email'
ACCESS_KEY = 'FCRpHzn8PugrkdWEHStNQDZh'
CREATE_USER_URL = 'https://api.movieterra.com/tickets'
GET_RECOMMENDATIONS_URL = 'https://api.movieterra.com/recommendations?user_id={}&access_key={}&city={}'


import logging
log_directory = 'log'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
ERROR_LOG = "{}/error.log".format(log_directory)
SUCCESS_LOG = "{}/success.log".format(log_directory)
ERROR_MAIL_LOG = "{}/error_mail.log".format(log_directory)
SUCCESS_LOG_FORMAT = ("%(asctime)s: %(message)s")
ERROR_LOG_FORMAT = ("%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d")
ERROR_MAIL_FORMAT = ("%(asctime)s : %(message)s")

error_formatter = logging.Formatter(ERROR_LOG_FORMAT)
success_formatter = logging.Formatter(SUCCESS_LOG_FORMAT)
error_mail_formatter = logging.Formatter(ERROR_MAIL_FORMAT)


def set_loggers():
    setup_logger('success_log', SUCCESS_LOG, logging.INFO, success_formatter)
    setup_logger('error_log', ERROR_LOG, logging.ERROR, error_formatter)
    setup_logger('error_mail_log', ERROR_MAIL_LOG,
                 logging.ERROR, error_mail_formatter)

def setup_logger(logger_name, log_file, level, formatter):
    log_setup = logging.getLogger(logger_name)
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    log_setup.setLevel(level)
    log_setup.addHandler(fileHandler)
    log_setup.addHandler(streamHandler)


def logger(msg, logfile='info'):
    if logfile == 'error':
        log = logging.getLogger('error_log')
        log.propagate = False
        log.error(msg)
    if logfile == 'error_mail':
        log = logging.getLogger('error_mail_log')
        log.propagate = False
        log.error(msg)
    if logfile == 'success':
        log = logging.getLogger('success_log')
        log.propagate = False
        log.info(msg)

def html_error_handler(html, user_id):
    logger('Error occured while processing user {}. Template will be saved in log/failed_html.'.format(user_id), 'error')
    if not os.path.exists('{}/failed_html'.format(log_directory)):
        os.makedirs('{}/failed_html'.format(log_directory))
    failed_html_name = '{}/failed_html/'.format(log_directory) + strftime(
        "%d%m%Y%H%M%S") + '_user_' + str(user_id) + '_failed.html'
    with open(failed_html_name, "w+") as f:
        f.write(html)

class Mailer():
    def __init__(self, user_id, movies, city=None):
        self.user_id = user_id
        self.movies = movies
        self.city = city
        self.movies_to_recommend = []
        self.recommendation_id = None

    def create_user(self):
        body = dict(access_key=ACCESS_KEY, user_id=self.user_id,movies=self.movies, city=self.city)
        response = requests.post(CREATE_USER_URL, data=json.dumps(body), headers=HEADERS)
        return response.status_code

    def get_recommendations(self):
        response = requests.get(GET_RECOMMENDATIONS_URL.format(self.user_id, ACCESS_KEY, self.city))  
        if response.status_code == 200:
            self.movies_to_recommend = response.json()['recommendations']
            if not self.movies_to_recommend:
                return 0 
            else:
                self.recommendation_id = response.json()['recommendation_id']
                return 1  
        else:
            logger(response.status_code, 'error')
            logger(response.reason, 'error')
            return 2 

    def form_characteristics(self):  
        body = dict(movies_to_recommend = self.movies_to_recommend, access_key = ACCESS_KEY, user_id = self.user_id)
        resp = requests.post(SOURCE_URL + '/template', data = json.dumps(body), headers=HEADERS)
        if resp.status_code == 200:
            response = resp.json()
            if response['error']:
                logger('Could not form html-template','error')
                return response['html'], False
            else:
                html = response['html']
                return html
        else:
            logger('Response status code while trying to get template: {}'.format(resp.status_code), 'error')
            try: 
                response = resp.json()
                return response['html'], False
            except: 
                return 


    def send_report(self): 
        body = dict(recommendation_id=self.recommendation_id)
        resp = requests.post(SOURCE_URL + '/report', data=json.dumps(body), headers=HEADERS)
        return resp.status_code

    def send_email(self, html, email):
        json_value = {
            'from': ESPUTNIK_USER,
            'subject': SUBJECT,
            'htmlText': html,
            'plainText': PLAIN_TEXT,
            'emails': [email]
        }
        resp = requests.post(url=EMAIL_API_METHOD, auth=HTTPBasicAuth(ESPUTNIK_USER, ESPUTNIK_PASSWORD), json=json_value)
        if resp.status_code == 200:
            logger(email + ', ' + str(self.movies_to_recommend) , 'success')
            self.send_report()
        else:
            msg = 'Esputnik returned code {}. Email wasn\'t sent. Template will be saved in log/failed_html.'.format(
                resp.status_code)
            logger('-' * 50, 'error_mail')
            logger(msg, 'error_mail')
            body = {
                'from': ESPUTNIK_USER,
                'subject': SUBJECT,
                'plainText': PLAIN_TEXT,
                'email': email
            }
            logger('-' * 25 + 'REQUEST: ' + '-' * 25, 'error_mail')
            for key, value in body.items():
                m = str(key) + ': ' + str(value)
                logger(m, 'error_mail')
            logger('Request Headers: {}'.format(resp.request.headers), 'error_mail')
            logger('-' * 25 + 'RESPONSE: ' + '-' * 25, 'error_mail')
            logger(' Headers', 'error_mail')
            for key, value in dict(resp.headers.items()).items():
                logger(str(key) + ': ' + str(value), 'error_mail')
            logger('-' * 25 + 'REASON: ' + '-' * 25, 'error_mail')
            logger(resp.reason, 'error_mail')
            logger(resp.text, 'error_mail')
            return
        return resp.status_code


def main(filename):
    users = []
    file = open(filename, 'r')
    reader = csv.reader(file)
    for user in reader:
        users.append(user)
    file.close()
    for user in users:
        if user == '' or user == []:
            continue
        user_id = user[0]
        email = re.sub('\'', '', user[1]) 
        city = user[2]
        user_movies = user[3:]
        if len(user_movies) == 1 and ',' in user_movies[0]:
            movies = [int(m) for m in user_movies[0].split(',')]
        else:
            movies = [int(m) for m in user[3:] if m != '']
        user_mail = Mailer(user_id, movies, city)
        created = user_mail.create_user()
        if created == 200:
            rec_status = user_mail.get_recommendations()
            if rec_status == 1:
                html = user_mail.form_characteristics()
                if html is None:
                    logger('Error while getting template for user {}.'.format(user_id), 'error')
                    continue
                if not isinstance(html, tuple):
                    esputnik_resp = user_mail.send_email(html, email)
                    if esputnik_resp != 200:
                        html_error_handler(html, user_id)
                        break  
                else: 
                    html_error_handler(html[0], user_id)
            if rec_status == 0:
                logger('Nothing to recommend to user {}.'.format(user_id), 'success')
                continue
            if rec_status == 2:
                logger('Error while getting recommendations for user {}.'.format(
                    user_id), 'error')
                continue
        else:
            logger('Failed to create user {}. Server returned {}.'.format(
                user_id, created), 'error')


if __name__ == "__main__":
    set_loggers()
    main(FILE_NAME)