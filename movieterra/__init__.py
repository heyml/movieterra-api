from flask import Flask
# from movieterra.models import db

def create_app():
    app = Flask(__name__)
    #with app.app_context():
        #db.init_app(app)
    return app

app = create_app()
