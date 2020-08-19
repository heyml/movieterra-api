from movieterra.models import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key = True)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    agent_user_id = db.Column(db.Text)
    agent_id = db.Column(db.Integer)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    city  = db.Column(db.Text)
    
    def __init__(self, created_at, updated_at, agent_user_id, agent_id, name, email,city):
        self.created_at = created_at
        self.updated_at = updated_at
        self.agent_user_id = agent_user_id
        self.agent_id = agent_id
        self.name = name
        self.email = email
        self.city = city
        
    def __repr__(self):
        return '<User>'