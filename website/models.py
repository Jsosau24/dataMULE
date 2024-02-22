# Imports
from . import db
from datetime import datetime
from flask_login import UserMixin

# Databse Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    colby_id = db.Column(db.Integer, unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity':'user',
        'polymorphic_on':type
    }

    team_associations = db.relationship('TeamUserAssociation', back_populates="user")

class Admin(User):

    __tablename__ = 'admin'
    colby_id = db.Column(db.Integer, db.ForeignKey('users.colby_id'), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity':'admin',
    }

class Peak(User):

    __tablename__ = 'peak'
    colby_id = db.Column(db.Integer, db.ForeignKey('users.colby_id'), primary_key=True)
    
    __mapper_args__ = {
        'polymorphic_identity':'peak',
    }

class Coach(User):

    __tablename__ = 'coaches'
    colby_id = db.Column(db.Integer, db.ForeignKey('users.colby_id'), primary_key=True)
    
    __mapper_args__ = {
        'polymorphic_identity':'coach',
    }

class Athlete(User):
    __tablename__ = 'athletes'
    
    colby_id = db.Column(db.Integer, db.ForeignKey('users.colby_id'), primary_key=True)
    hawkin_api_id = db.Column(db.String, nullable=True)
    status = db.Column(db.Integer)
    gender = db.Column(db.String(50))
    class_year = db.Column(db.Integer)
    position = db.Column(db.String(50))
    
    # Maxes for calculations 
    jh_max = db.Column(db.Integer)
    rfd_max = db.Column(db.Integer)
    mrsi_max = db.Column(db.Integer)
    ppf_max = db.Column(db.Integer)

    __mapper_args__ = {
        'polymorphic_identity':'athlete',
    }

class AthletePerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)

    jump_height = db.Column(db.Float, nullable=False)
    braking_rfd = db.Column(db.Float, nullable=False)  # Rate of Force Development
    mrsi = db.Column(db.Float, nullable=False)  # Modified Reactive Strength Index
    peak_propulsive_force = db.Column(db.Float, nullable=False)

    # Foreign key to link performance data to an athlete
    athlete_id = db.Column(db.Integer, db.ForeignKey('athletes.colby_id'), nullable=False)

    # Relationship (this line is needed if you want to access performance data from the Athlete model)
    athlete = db.relationship('Athlete', backref=db.backref('performances', lazy=True))

    def __repr__(self):
        return f"<AthletePerformance {self.id}, Date: {self.date}, Athlete ID: {self.athlete_id}>"

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # Maxes for calculations 
    jh_max = db.Column(db.Integer)
    rfd_max = db.Column(db.Integer)
    mrsi_max = db.Column(db.Integer)
    ppf_max = db.Column(db.Integer)

    team_associations = db.relationship('TeamUserAssociation', back_populates="team")

class TeamUserAssociation(db.Model):
    __tablename__ = 'team_members'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), primary_key=True)
    role = db.Column(db.String(50))
    
    user = db.relationship(User, back_populates="team_associations")
    team = db.relationship(Team, back_populates="team_associations")

class TeamPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    avg_jump_height = db.Column(db.Float, nullable=False)  # Average jump height
    avg_braking_rfd = db.Column(db.Float, nullable=False)  # Average Rate of Force Development
    avg_mrsi = db.Column(db.Float, nullable=False)  # Average Modified Reactive Strength Index
    avg_peak_propulsive_force = db.Column(db.Float, nullable=False)  # Average Peak Propulsive Force

    # Foreign key to link performance data to a team
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)

    # Relationship (this line is needed if you want to access performance data from the Team model)
    team = db.relationship('Team', backref=db.backref('performances', lazy=True))

    def __repr__(self):
        return f"<TeamPerformance {self.id}, Date: {self.date}, Team ID: {self.team_id}>"

class Note(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign Keys
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('athletes.colby_id'))

    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_notes')
    receiver = db.relationship('Athlete', foreign_keys=[receiver_id], backref='received_notes')


