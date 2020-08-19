from movieterra.models import db

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key = True)
    created_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer)
    agent_id = db.Column(db.Integer)
    delivered = db.Column(db.Boolean)

    def __init__(self, user_id, agent_id, created_at, delivered = 0):
        self.user_id = user_id
        self.agent_id = agent_id
        self.created_at = created_at
        self.delivered = delivered
    
    def __repr__(self):
        return '<Recommendation %r>' % self.user_id + ' ' + str(self.agent_id)