# methods on the file (you can look these up and it will take you there)
## create_app --> create the webpage function
## create_database --> created the database
## create_dummy_users --> created a dummy database

# imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from os import path
from flask import Flask
from flask_login import current_user
from dotenv import load_dotenv
import os

def configure():
    load_dotenv()

configure()

secret_key = os.getenv('secret_key')

# Initialize the extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
    app.config['SECRET_KEY'] = secret_key

    # Initialize extensions with the app
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # Register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .routes import routes as routes_blueprint
    app.register_blueprint(routes_blueprint)

    # Setup code moved here
    with app.app_context():
        if not path.exists('website/database.db'):
            # Assuming create_database is a function you've defined to initialize your database
            create_database(app)
            create_dummy_users(app)
        # You can also call a function here to create dummy users or any other initial setup

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    @app.context_processor
    def inject_teams():
        from .models import Team
        from flask_login import current_user
        if current_user.is_authenticated and current_user.type == 'admin':
            teams = Team.query.all()
        else:
            teams = None
        return dict(teams=teams)

    return app

def create_database(app):
    with app.app_context():
        db.create_all()
        print('Created Database')

def create_dummy_users(app):
    with app.app_context():
        from .models import Admin, Peak, Coach, Athlete, Team, TeamUserAssociation
    
    # Admin
    user = Admin.query.first()
    if not user:
        dummy = Admin(colby_id = 0,
                    first_name = "Admin",
                    last_name = 'User',
                    password = generate_password_hash('test'),
                    email = "admin@colby.edu"
                    )
        db.session.add(dummy)
        db.session.commit()
        
    # Peak
    user = Peak.query.first()
    if not user:
        dummy = Peak(colby_id = 1,
                    first_name = "Peak",
                    last_name = 'User',
                    password = generate_password_hash('test'),
                    email = "peak@colby.edu"
                    )
        db.session.add(dummy)
        db.session.commit()
        
    # Coach
    user = Coach.query.first()
    if not user:
        dummy = Coach(colby_id = 2,
                    first_name = "Coach",
                    last_name = 'User',
                    password = generate_password_hash('test'),
                    email = "coach@colby.edu"
                    )
        db.session.add(dummy)
        db.session.commit()
        
    # Athlete
    user = Athlete.query.first()
    if not user:
        dummy = Athlete(colby_id = 3,
                    first_name = "Athlete",
                    last_name = 'User',
                    password = generate_password_hash('test'),
                    email = "athlete@colby.edu",
                    status = 0,
                    gender = 'Male',
                    class_year = 2024,
                    position = 'Other'
                    )
        db.session.add(dummy)
        db.session.commit()

    team = Team.query.first()
    if not team:
        dummy_team = Team(
            name="Dummy Team",
        )
        db.session.add(dummy_team)
        db.session.commit()

        dummy_admin_association = TeamUserAssociation(
            user=Admin.query.first(),
            team=dummy_team,
            role='admin'
        )
        dummy_peak_association = TeamUserAssociation(
            user=Peak.query.first(),
            team=dummy_team,
            role='peak'
        )
        dummy_coach_association = TeamUserAssociation(
            user=Coach.query.first(),
            team=dummy_team,
            role='coach'
        )
        dummy_athlete_association = TeamUserAssociation(
            user=Athlete.query.first(),
            team=dummy_team,
            role='athlete'
        )

        db.session.add(dummy_admin_association)
        db.session.add(dummy_peak_association)
        db.session.add(dummy_coach_association)
        db.session.add(dummy_athlete_association)
        db.session.commit()
        pass

    