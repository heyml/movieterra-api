'''
    Этот скрипт запускается каждое утро в 9:00 и обновляет бд
'''
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d",
    datefmt = '%d/%m/%Y %H:%M:%S',
    filename = '/home/movieterra/mvt/movieterra/log/updater.log'
)

logger = logging.getLogger(__name__)
handler = RotatingFileHandler('/home/movieterra/mvt/movieterra/log/updater.log', maxBytes=2000, backupCount=10)
logger.addFilter(handler)

logger.info('#' * 120)
logger.info('{} started'.format('Updater'))


from datetime import datetime # костыльно, простите
with open('../updater_dates.txt','a') as f:
    f.write(str(datetime.now()) + '\n')

from movieterra.updaters.updater import check_for_updates
logger.info('Started checking for updates...')
check_for_updates('planetakino', logger)
check_for_updates('vkino', logger)
