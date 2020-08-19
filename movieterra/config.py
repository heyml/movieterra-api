from movieterra import app

ENVIRONMENT = 'development'
# SQLALCHEMY_DATABASE_URI = ('mysql+pymysql://ai:MachineLearning128@127.0.0.1/movies_dev')
# SQLALCHEMY_DATABASE_URI = ('mysql+pymysql://ai:MachineLearning128@192.168.0.112/movies_dev')
SQLALCHEMY_DATABASE_URI = ('mysql+pymysql://root:root@127.0.0.1/movies_dev1')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://ai:MachineLearning128@192.168.0.112/movies_dev'
# cnx = create_engine('mysql+pymysql://ai:MachineLearning128@192.168.0.112/movies_development?charset=utf8', encoding='utf8', echo=False)
