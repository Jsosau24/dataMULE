"""
Jonathan Sosa 
helper_functions.py
may-jun 2023
"""

# functions on the file (you can look these up and it will take you there)
## create_user --> creates an user if it doesn't exist
##create_user_csv --> creates users using a CSV file
## get_file_extension --> returns the extension of a file

#imports
from werkzeug.security import generate_password_hash
from .models import Peak, Athlete, Coach, Admin, User, TeamUserAssociation, Team
from werkzeug.utils import secure_filename
import pandas as pd
import os
from . import db
from .email import *

#functions
from werkzeug.security import generate_password_hash

def create_user(colby_id, first_name, last_name, email, gender, class_year, user_type, hawkin_api_id=None, team_name=None):
    """
    This function creates new users and optionally associates them with a team.
    """
    used_email = User.query.filter_by(email=email).first()

    if used_email:
        print("Email already used")
        return False, [colby_id, 'user exists']

    password = generate_password_hash('Colby')
    new_user = None

    try:
        if user_type == 'admin':
                new_user = Admin(
                colby_id=colby_id, 
                first_name=first_name, 
                last_name=last_name, 
                email=email, 
                password=password)
        elif user_type == 'peak':
                new_user = Peak(
                colby_id=colby_id, 
                first_name=first_name, 
                last_name=last_name, 
                email=email, 
                password=password)
        elif user_type == 'coach':
                new_user = Coach(
                colby_id=colby_id, 
                first_name=first_name, 
                last_name=last_name, 
                email=email, 
                password=password)
        elif user_type == 'athlete':
            print("Creating athlete")
            new_user = Athlete(
                colby_id=colby_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                gender=gender,
                class_year=class_year,
                hawkin_api_id=hawkin_api_id,  
                status=0,
                position='Other'
            )
        else:
            print("Invalid user type")  # Debugging
            return False, [colby_id, 'wrong type of user']

        token = generate_password_reset_token(email)
        
        # Generate URL for setting password
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        # Send email with password reset link
        send_email(email, 'Set Your Password', 'mail/password_reset', reset_url=reset_url)

        # Add user to the database
        db.session.add(new_user)
        db.session.flush()  # This will assign an ID to new_user

        # If team_name is provided, create a TeamUserAssociation
        if team_name:
            team = Team.query.filter_by(name=team_name).first()
            if team:
                association = TeamUserAssociation(team=team, user=new_user, role=user_type)
                db.session.add(association)
            else:
                print(f"Team not found with name: {team_name}")  # Debugging
                return False, [colby_id, f'team not found: {team_name}']

        db.session.commit()
        print("User created successfully")  # Debugging
        return True, new_user

    except Exception as e:
        print(f"Error in create_user: {e}")  # Debugging
        return False, [colby_id, "error in create_user function: " + str(e)]
