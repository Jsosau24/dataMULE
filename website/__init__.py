# methods on the file (you can look these up and it will take you there)
## create_app --> create the webpage function
## create_database --> created the database
## create_dummy_users --> created a dummy database

# imports
from flask import Flask, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from os import path
from flask import Flask
from flask_login import current_user
from dotenv import load_dotenv
import os
import requests
from flask_apscheduler import APScheduler
import time
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from .email import mail
from flask_mail import Mail

def configure():
    load_dotenv()

configure()

secret_key = os.getenv('secret_key')
email_pass = os.getenv('email_pass')

# Initialize the extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
    app.config['SECRET_KEY'] = secret_key

    # Configure Flask-Mail...
    app.config['MAIL_SERVER'] = 'smtp.office365.com'  # Use Microsoft's SMTP server
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'data.mule2024@outlook.com'
    app.config['MAIL_PASSWORD'] = email_pass
    app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT')

    # Initialize extensions with the app
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    mail.init_app(app)

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
    

    # Scheduler setup
    scheduler = APScheduler()
    scheduler.init_app(app)
    
    @scheduler.task('interval', id='pull_data_task', seconds=100, misfire_grace_time=10)
    def scheduled_task():
        with app.app_context():
            update_db()
            print('databse updated')
        

    scheduler.start()

    return app

def get_access_token():
    ''' collects the access token'''
    load_dotenv()
    refresh_token = os.getenv('refresh_token')

    # Get Access token
    headers = {'Authorization': f'Bearer {refresh_token}'}
    auth_response = requests.get('https://cloud.hawkindynamics.com/api/token', headers=headers)
    auth_response.raise_for_status()  
    return (auth_response.json().get('access_token'))

def update_db():
    ''' Function to update the databse constantly'''

    # Get the current UNIX timestamp
    now = int(time.time())
    load_dotenv()
    last = os.getenv('api_last_update')
    update_env_file('.env', 'api_last_update', now)
    print(now)
    print(last)

    access_token = get_access_token()

    url = f'https://cloud.hawkindynamics.com/api/colby?from={last}&to={now}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    data  = requests.get(url, headers=headers)
    data = data.json()
    data = data['data']

    from .models import Athlete, AthletePerformance

    for jump in data:
        # Collects the data from the API
        athlete = Athlete.query.filter_by(hawkin_api_id=jump['athlete']['id']).first()
        if athlete:
            existing_record = AthletePerformance.query.filter_by(
                athlete_id=athlete.colby_id, 
                date=datetime.utcfromtimestamp(jump['timestamp'])
            ).first()

            if not existing_record:
                try:
                    j = AthletePerformance(
                        date=datetime.utcfromtimestamp(jump['timestamp']),
                        jump_height=jump['Jump Height(m)'],
                        braking_rfd=jump['Braking RFD(N/s)'],
                        mrsi=jump['mRSI'],
                        peak_propulsive_force=jump['Peak Propulsive Force(N)'],
                        athlete_id=athlete.colby_id  
                    )
                    db.session.add(j)
                except:
                    pass

        try:
            db.session.commit()
            # Instead of using flash, consider logging the success message
            #app.logger.info('Athlete performance data added successfully.')
        except SQLAlchemyError as e:
            db.session.rollback()
            # Log the error instead of using flash
            #app.logger.error('Error adding performance data: {}'.format(e))

        # Current end date
        end_date = datetime.today().date()
        start_date = datetime(end_date.year, 8, 1).date()

        # Check if the start date is later in the year than the end date
        if start_date > end_date:
            # If so, set the start date to August 1st of the previous year
            start_date = datetime(end_date.year - 1, 8, 1).date()

        try:

            set_max(athlete.colby_id, start_date, end_date)

        except:
            pass

        try:
            team_associations = athlete.team_associations
            teams = [association.team for association in team_associations]

            for team in teams:
                set_max_team(team.id, start_date, end_date)
        except:
            pass

    return

def set_max(athlete_id, start_date, end_date):
    '''Sets the max values for the athletes'''
    from .models import Athlete, AthletePerformance
    max_values = db.session.query(
        func.max(AthletePerformance.jump_height).label('max_jump_height'),
        func.max(AthletePerformance.braking_rfd).label('max_braking_rfd'),
        func.max(AthletePerformance.mrsi).label('max_mrsi'),
        func.max(AthletePerformance.peak_propulsive_force).label('max_peak_propulsive_force')
    ).filter(
        AthletePerformance.athlete_id == athlete_id,
        AthletePerformance.date >= start_date,
        AthletePerformance.date <= end_date
    ).first()

    if max_values[0] == None:
        max_values = db.session.query(
        func.max(AthletePerformance.jump_height).label('max_jump_height'),
        func.max(AthletePerformance.braking_rfd).label('max_braking_rfd'),
        func.max(AthletePerformance.mrsi).label('max_mrsi'),
        func.max(AthletePerformance.peak_propulsive_force).label('max_peak_propulsive_force')
        ).filter(
            AthletePerformance.athlete_id == athlete_id,
        ).first()

    a = Athlete.query.filter_by(colby_id=athlete_id).first()
    if a:
        a.jh_max = max_values[0]
        a.rfd_max = max_values[1]
        a.mrsi_max = max_values[2]
        a.ppf_max = max_values[3]

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()  
            print(f"Error updating athlete: {e}")
    else:
        print("Athlete not found")

    return

def set_max_team(team_id, start_date, end_date):
    from .models import Team, AthletePerformance
    '''Sets the max for the team'''
    team = Team.query.get(team_id)
    team_members = [association.user for association in team.team_associations]
    athletes = [member for member in team_members if member.type == 'athlete']
    colby_ids = [athlete.colby_id for athlete in athletes]

    max_values = db.session.query(
        func.max(AthletePerformance.jump_height).label('max_jump_height'),
        func.max(AthletePerformance.braking_rfd).label('max_braking_rfd'),
        func.max(AthletePerformance.mrsi).label('max_mrsi'),
        func.max(AthletePerformance.peak_propulsive_force).label('max_peak_propulsive_force')
    ).filter(
        AthletePerformance.athlete_id.in_(colby_ids),  
        AthletePerformance.date >= start_date,
        AthletePerformance.date <= end_date
    ).first()

    if team:
        team.jh_max = max_values[0]
        team.rfd_max = max_values[1]
        team.mrsi_max = max_values[2]
        team.ppf_max = max_values[3]

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()  
            print(f"Error updating Team: {e}")

    return

def update_env_file(env_file_path, key, new_value):
    """Update or add an environment variable in the .env file."""
    # Attempt to read the existing lines
    try:
        with open(env_file_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        lines = []
    
    # Check if the key exists and update it
    key_found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={new_value}\n"
            key_found = True
            break
    
    # If the key wasn't found, append it
    if not key_found:
        lines.append(f"{key}={new_value}\n")
    
    # Write the changes back to the .env file
    with open(env_file_path, 'w') as file:
        file.writelines(lines)



#---------------------------

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

    