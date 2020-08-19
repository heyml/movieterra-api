import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level = logging.DEBUG,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    # format = '%(level)s %(asctime)s %(message)s',
    #  format="%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d",
    datefmt = '%d/%m/%Y %H:%M:%S',
    filename = 'movieterra/log/app.log'
)

logger = logging.getLogger(__name__)
handler = RotatingFileHandler('movieterra/log/app.log', maxBytes=2000, backupCount=10)
logger.addFilter(handler)


logger.info('-' * 120)
logger.info('{} started'.format('App'))

import requests
from flask import request, jsonify, Response, abort, url_for

from movieterra import app

from movieterra.models import *
from movieterra.models.user import User
from movieterra.models.ticket import Ticket
from movieterra.models.agent import Agent
from movieterra.models.recommendation import Recommendation

from movieterra.recommenders.recommender import Recommender

from movieterra.workers.user_schema import update_user_row, insert_user_row, insert_recommendation_row, sort_by_dates
from movieterra.workers.poster_image import create_local_poster
from movieterra.workers.template import form_table_items, render_template

#from movieterra.task import set_scheduler

@app.errorhandler(403)
def access_key_required(not_in_db = False):
    ''' Handler to control access rights '''
    code = 403
    if not_in_db:
        description = '403 Forbidden. Unknown access key.\n'
        logger.error(description)
        # print(description)
    else:
        description = '403 Forbidden. Specify Access Key.\n'
        logger.error(description)
        # print(description)
    return description, code

@app.errorhandler(400)
def bad_request(user = False, data = ''):
    ''' Handler to check input '''
    code = 400
    if user:
        description = '400 Bad Request. Unknown user.\n'
        logger.error(description)
        # print(description)
    else:
        description = '400 Bad Request. Wrong input.\n'
        logger.error(description)
        # print(description)
    if data != '':
        description = data
        logger.error(data)
        # print(data)
    return description, code

@app.route('/')
def index():
    ''' Root of the api '''
    logger.info('/welcome')
    welcome_message = 'Welcome to movieterra API! Use /tickets to create user and /recommendations to get recommendations.\n'
    return welcome_message

@app.route('/tickets', methods=['POST'])
def tickets():
    ''' 
        Method for creating/updating user in database.
        Recieves user parameters which are specified in User ORM model.
        Required parameters: access_key, user_id
    '''
    logger.info('=' * 100)
    if request.method == 'POST':
        data = request.get_json()
        logger.info('/tickets request: ' + str(data))
        if data.get('access_key') is None:
            return access_key_required(not_in_db = False)
        agent = Agent.query.filter_by(access_key = data.get('access_key')).first() 
        if agent is None: 
            return access_key_required(not_in_db = True)
        if data.get('user_id') is None: # не указан ид польз. в их системе // agent_user_id
            return bad_request()
    user = User.query.filter_by(agent_user_id = data.get('user_id'), agent_id = agent.id).first()
    if user:
        logger.info('Updating user {} in db'.format(str(user.agent_user_id)))
        return update_user_row(data, user, logger)
    else:
        logger.info('Creating new user {} in db'.format(data.get('user_id')))
        return insert_user_row(data, agent, logger)

@app.route('/recommendations', methods=['GET'])
def get_recommendations():
    '''
        Method for getting recommendations for user which is already in database.
        Required parameters: access_key, user_id
        In case of success (recommendations are generated and are not empty)
        recommendation_id is written to database.
    '''
    logger.info('=' * 100)
    data = request.args
    logger.info('/recommendations request: ' + str(data))
    if data.get('access_key') is None:
        return access_key_required()

    agent = Agent.query.filter_by(access_key = data.get('access_key')).first() 
    if agent is None: 
        return access_key_required(not_in_db = True)
    elif not data.get('user_id'):
        return bad_request()
    
    user = User.query.filter_by(agent_user_id = data.get('user_id'), agent_id = agent.id).first()
    if user:
        logger.info('Forming recommendations for user {}...'.format(user.id))
        result = Recommender(user, agent, logger).recommend()  
        if result:
            result = [r['agent_movie_id'] for r in result[:3]]
            result = sort_by_dates(result, agent.agent_name)
            logger.debug('Recommendations result: {}'.format(str(result)))
            recommendation_id = insert_recommendation_row(user, agent, result)       
            return jsonify(recommendations = result, recommendation_id = recommendation_id)  
        else:
            logger.debug('No recommendations for user {}'.format(user.id))
            return jsonify(recommendations = result)       
    else:
        return bad_request(user = True)
    #logger.info('Generationg recommendations for user {}'.format(user.id))
    return 'Працює\n'

@app.route('/report', methods=['POST'])
def report():
    '''
        Method for reports from agent-mailers.
        If email with recommendations was delivered to user,
        agent sends report.
    '''
    logger.info('=' * 100)
    data = request.get_json()
    rec_id = int(data.get('recommendation_id'))
    user_rec = Recommendation.query.filter_by(id = rec_id).first()
    if user_rec is not None:
        user_rec.delivered = 1
        db.session.commit()
        logger.info('Delivered mail for user {}'.format(user_rec.user_id))
        return "200"
    else:
        logger.info('Not delivered mail for user {}'.format(user_rec.user_id))
        abort(400)
 
@app.route('/poster', methods=['POST'])
def create_poster():
    '''
        Method for generating poster.
        When agent-mailer requests '/tempalte' and while generating template
        it cant'find a poster at api.movieterra.com,
        it sends a request to generate it.
    '''
    logger.info('=' * 100)
    data = request.get_json() # access_key, filename, vkino_poster_url, month, day
    logger.info('/poster request: {}'.format(str(data)))
    access_key = str(data.get('access_key'))
    if not access_key:
        return access_key_required()
    filename = data.get('filename')
    vkino_poster_url = data.get('vkino_poster_url')
    month = data.get('month')
    day = data.get('day')
    if vkino_poster_url != '' and vkino_poster_url is not None:
        poster_url = create_local_poster(vkino_poster_url, month, day, filename)
        print(poster_url)
        if requests.get(poster_url).status_code != 200:
            return bad_request()
        else:
            return poster_url

@app.route('/template', methods=['POST'])
def template():
    '''
        Method for creating email-html template. 
        Request cames from agent-mailer.
        
        Parameters:
        access_key, user_id, movies_to_recommend
        Returns: 
        json-object with html-file and error status.

    '''
    logger.info('=' * 100)
    data = request.get_json() 
    logger.info('/template request: ' + str(data))
    access_key = str(data.get('access_key'))
    if not access_key:
        return access_key_required()
    logger.info('Request to form html file for user {}'.format(str(data.get('user_id'))))
    movies_to_recommend = list(data.get('movies_to_recommend'))
    table_items = form_table_items(movies_to_recommend, logger) 
    if type(table_items) is list:
        error = False
        for md in table_items:
            '''
                если хоть одно значение None, то темплейт
                сформировался неправильно и емеил отправлять
                нельзя
            '''
            if None in md.values(): 
                error = True
        context = dict(table_items = table_items)
        html = render_template(context)
        if error:
            logger.error('Something went wrong in cycle, returning error status')
            ''' 
                даже битый html нужно отправлять, он сохраняется у них в логах
            '''
            return jsonify(html = html, error = True) 
            #with open('file.html', 'w+') as f:
            #    f.write(html)
        else:
            logger.info('EVERYTHING OK, RETURNING HTML !!!')
            #with open('file.html', 'w+') as f:
            #    f.write(html)
            return jsonify(html = html, error = False) 
    else:
        #with open('file.html', 'w+') as f:
        #        f.write(table_items['html'])
        return jsonify(table_items) # это html, но битый, все параметры -  null

