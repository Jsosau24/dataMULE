from dotenv import load_dotenv
import os
import requests
import time
from .models import *
from . import db
from sqlalchemy import func
from datetime import datetime, timedelta
from flask import flash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import time

def get_access_token():
    ''' collects the access token'''
    load_dotenv()
    refresh_token = os.getenv('refresh_token')

    # Get Access token
    headers = {'Authorization': f'Bearer {refresh_token}'}
    auth_response = requests.get('https://cloud.hawkindynamics.com/api/token', headers=headers)
    auth_response.raise_for_status()  
    return (auth_response.json().get('access_token'))

def get_athlete_data(hawkin_api_id):
    ''' Collect the data from an individual athlete'''
    access_token = get_access_token()
    url = f'https://cloud.hawkindynamics.com/api/colby?athleteId={hawkin_api_id}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    data  = requests.get(url, headers=headers)
    return(data.json())
    
def update_db():
    ''' Function to update the databse constantly'''

    print('inside')

    # Get the current UNIX timestamp
    now = int(time.time())

    load_dotenv()
    last = os.getenv('api_last_update')

    update_env_file('.env', 'api_last_update', now)

    access_token = get_access_token()

    url = f'https://cloud.hawkindynamics.com/api/colby?from={last}&to={now}'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    data  = requests.get(url, headers=headers)
    data = data.json()
    data = data['data']

    for jump in data:
        # Collects the data from the API
        athlete = Athlete.query.filter_by(hawkin_api_id=jump['athlete']['id']).first()
        print(athlete)

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
            flash('Athlete performance data added successfully.', 'success')
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Error adding performance data.', 'error')

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
            print("Athlete updated successfully")
        except Exception as e:
            db.session.rollback()  
            print(f"Error updating athlete: {e}")
    else:
        print("Athlete not found")

    return

def set_max_team(team_id, start_date, end_date):
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
            print("Team updated successfully")
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




