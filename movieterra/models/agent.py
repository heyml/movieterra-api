from movieterra.models import db

class Agent(db.Model):
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_name = db.Column(db.String(255))
    access_key = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)

    def __init__(self, agent_name, access_key, created_at):
        self.agent_name = agent_name
        self.access_key = access_key
        self.created_at = created_at

    def __repr__(self):
        return '<Agent %r>' % self.agent_name