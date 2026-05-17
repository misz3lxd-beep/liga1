import os
from datetime import datetime
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Inteligentne wykrywanie środowiska (Lokalnie vs Azure)
if 'WEBSITE_SITE_NAME' in os.environ:
    db_path = '/home/site/liga1.db'
else:
    db_path = 'liga1.db'

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================
# MODELE BAZY DANYCH (Zgodnie z Diagramem Klas)
# ==========================================

class League(db.Model):
    __tablename__ = 'leagues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    schedule = db.relationship('Schedule', backref='league', uselist=False, cascade="all, delete-orphan")
    teams = db.relationship('Team', backref='league', lazy=True)
    players = db.relationship('Player', backref='league', lazy=True)

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'), nullable=False)
    
    games = db.relationship('Game', backref='schedule', lazy=True, cascade="all, delete-orphan")

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    time_zone_id = db.Column(db.String(50), nullable=False)
    
    games = db.relationship('Game', backref='location', lazy=True)

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'), nullable=False)
    
    players = db.relationship('Player', backref='team', lazy=True)

class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_and_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    visitor_team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    
    home_team = db.relationship('Team', foreign_keys=[home_team_id])
    visitor_team = db.relationship('Team', foreign_keys=[visitor_team_id])
    
    score = db.relationship('Score', backref='game', uselist=False, cascade="all, delete-orphan")

class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    home_score = db.Column(db.Integer, nullable=False, default=0)
    visitor_score = db.Column(db.Integer, nullable=False, default=0)


# Automatyczne tworzenie struktury bazy danych przy starcie
with app.app_context():
    db.create_all()

# ==========================================
# TRASY / WIDOKI
# ==========================================

@app.route('/')
def home():
    return "Aplikacja Liga1 działa i baza danych została pomyślnie zainicjalizowana!"

if __name__ == '__main__':
    app.run(debug=True)
