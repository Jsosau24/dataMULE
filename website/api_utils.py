from dotenv import load_dotenv
import os
import requests
from .models import *
from . import db
from sqlalchemy import func
from datetime import datetime, timedelta

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
    test  = requests.get(url, headers=headers)
    return(test.json())
    
def parse_jump_data(data, db):
    '''Parse the data form the API and sets it to a more manage format'''

    data = data['data']
    clean_data = [['hawking-id'],['Timestamp'],['Jump Height'],['Braking RFD'],['Peak Propulsive Force'],['mRSI']]

    for jump in data:

        athlete_id = jump['athlete']['id']
        timestamp = jump['timestamp']
        jh = jump['Jump Height(m)']
        rfd = jump['Braking RFD(N/s)']
        ppf = jump['Peak Propulsive Force(N)']
        mrsi = jump['mRSI']

    return(clean_data)

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





