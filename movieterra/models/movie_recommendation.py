from movieterra.models import db

class MovieRecommendation(db.Model):
    __tablename__ = 'movies_recommendations';
    
    id = db.Column(db.Integer, primary_key = True)
    recommendation_id = db.Column(db.Integer)
    movie_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    
    def __init__(self, recommendation_id, movie_id, created_at):
        self.recommendation_id = recommendation_id
        self.movie_id = movie_id
        self.created_at = created_at