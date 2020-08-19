from flask_sqlalchemy import SQLAlchemy
from movieterra import app

# test/debug only
###
import warnings
warnings.filterwarnings('ignore')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ai:MachineLearning128@192.168.0.112/movies_dev'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ai:MachineLearning128@127.0.0.1/movies_dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@127.0.0.1/movies_dev1'
###

db = SQLAlchemy(app) 
