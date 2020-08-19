from movieterra.models import db

class Vkino(db.Model):
    __tablename__ = 'vkino_movies'
    
    id = db.Column(db.Integer, primary_key = True)
    agent_movie_id = db.Column(db.Integer)
    tmdb_fk_id = db.Column(db.Integer)
    is_actual = db.Column(db.Boolean)
    is_premiere = db.Column(db.Boolean)
    year = db.Column(db.SmallInteger)
    name = db.Column(db.Text)
    nameoriginal = db.Column(db.Text)
    dates = db.Column(db.Text)
    release_date = db.Column(db.DateTime)    
    city = db.Column(db.Text)

    def __init__(self, agent_movie_id, tmdb_fk_id=None, is_actual=0, is_premiere=None, year=None, name=None, nameoriginal=None,dates=None, release_date=None, city=None):
        self.agent_movie_id = agent_movie_id
        self.tmdb_fk_id = tmdb_fk_id
        self.is_actual = is_actual
        self.is_premiere = is_premiere
        self.year = year
        self.name = name
        self.nameoriginal = nameoriginal
        self.dates = dates
        self.release_date = release_date
        self.city = city