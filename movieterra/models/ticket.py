from movieterra.models import db

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    movie_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    
    def __init__(self, user_id, movie_id, created_at, updated_at):
        self.user_id = user_id
        self.movie_id = movie_id
        self.created_at = created_at
        self.updated_at = updated_at