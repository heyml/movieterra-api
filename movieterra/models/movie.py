from movieterra.models import db

class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key = True)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    tmdb_id = db.Column(db.Integer)
    poster_path = db.Column(db.String(255))
    director = db.Column(db.String(255))
    novel = db.Column(db.String(255))
    actors = db.Column(db.String(255))
    budget = db.Column(db.Integer)
    genres = db.Column(db.String(255))
    kwords = db.Column(db.Text)
    runtime = db.Column(db.Integer)
    title = db.Column(db.String(255))

    def __init__(self, created_at, updated_at, tmdb_id, poster_path, \
                 director, novel,actors,budget,genres,kwords,runtime, title):
        self.created_at = created_at 
        self.updated_at = updated_at
        self.tmdb_id = tmdb_id
        self.poster_path = poster_path
        self.director = director
        self.novel = novel
        self.actors = actors
        self.novel = novel
        self.actors = actors
        self.budget = budget
        self.genres = genres
        self.kwords = kwords
        self.runtime = runtime
        self.title = title
        
    def __repr__(self):
        return '<Movie %r>' % self.title