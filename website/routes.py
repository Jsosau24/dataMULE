"""
Jonathan Sosa 
routes.py
may-jun 2023
"""

# routes on the file (you can look these up and it will take you there)
## home --> redirects each user to their homepage
## athlete --> athlete view or athlete main page
## team --> team dasboard everyone but athelte has access
## athlete_coach --> view of an athelte from any other user but athlete
## admin_dashboard --> main view for an admin
## team_edit_dashboard --> dashboard with all the teams where you can select one to edit it
## update_position --> edit the position of an athlete from the team dashboard
## user_edit_dashboard --> dashboard with all the users where you can chose one to edit it
## user_edit --> handles the edits on any user
## team_edit --> page where you can choose users on a team
## update_team --> backend for updating the team
## new_note --> creates a new note
## notes_dashboard --> dasboard with all the notes created by the user
## update_note_visibility --> handles the backend to change the visibility of a note
## new_user --> route to create a new user
## new_user_csv --> creates a number of users using an CSV file
## remove_user --> removes a user form the db

# Imports
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from .models import Peak, Team, Athlete, User, Note, Coach, TeamUserAssociation
from . import db
from website.helper_functions import create_user
import pandas as pd
from flask import current_app
import csv
import io
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

#Flask blueprint
routes = Blueprint('main', __name__)

#routes
@routes.route('/')
def home():

    user = current_user

    if user.type == "admin":
        # Ensure the current user is an admin
        if current_user.type != "admin":
            return "<h1>NO ACCESS</h1>"

        # Query all athletes and teams
        athletes = User.query.filter_by(type='athlete').all()
        teams = Team.query.all()

        return render_template('admin_dashboard.html', athletes=athletes, teams=teams, user=user)
    
    elif user.type == "peak":
        peak = Peak.query.filter_by(colby_id=current_user.colby_id).first()
        team_association = next((association for association in peak.team_associations if association.role == 'peak'), None)
        
        if team_association is not None:
            team = team_association.team
            athletes = [association.user for association in team.team_associations if association.role == 'athlete']
        else:
            return "<h1>There are no teams</h1>"
    
        return render_template('team_dashboard.html', user=user,team=team, athletes=athletes)
    
    elif user.type == "coach":

        coach = Coach.query.filter_by(colby_id=current_user.colby_id).first()
        team_association = next((association for association in coach.team_associations if association.role == 'coach'), None)
        
        if team_association is not None:
            team = team_association.team
            athletes = [association.user for association in team.team_associations if association.role == 'athlete']
        else:
            return "<h1>There are no teams</h1>"
    
        return render_template('team_dashboard.html', user=user,team=team, athletes=athletes)
    
    elif user.type == "athlete":
        visible_notes = [note for note in current_user.received_notes if note.visible]
        return render_template('athlete_dashboard.html', athlete=current_user, user=current_user, notes=visible_notes)
    
    return render_template('login.html')

@routes.route('/athlete')
@login_required
def athlete():
    if current_user.type != "athlete":
        return "<h1>NO ACCESS</h1>"
    
    visible_notes = [note for note in current_user.received_notes if note.visible]

    return render_template('athlete_dashboard.html', athlete=current_user, user=current_user, notes=visible_notes)

@routes.route('/team/<int:id>', methods = ['GET', 'POST'])
@login_required
def team(id):

    if current_user.type == "athlete":
        return "<h1>NO ACCESS</h1>"
    
    team = Team.query.get(id)

    # Use the association table to get all users in the team
    team_members = [association.user for association in team.team_associations]

    # Filter only athletes if needed
    athletes = [member for member in team_members if member.type == 'athlete']

    return render_template('team_dashboard.html', team=team, athletes=athletes, user=current_user, current_team_id=id)

@routes.route('/athlete/<int:id>', methods = ['GET', 'POST'])
@login_required
def athlete_coach(id):

    if current_user.type == "athlete":
        return "<h1>NO ACCESS</h1>"
    
    athlete = Athlete.query.get(id)
    visible_notes = [note for note in athlete.received_notes if note.visible]

    return render_template('athlete_dashboard.html', athlete=athlete, user=current_user, notes=visible_notes)

@routes.route('/admin-dashboard')
@login_required
def admin_dashboard():

    # Ensure the current user is an admin
    if current_user.type != "admin":
        return "<h1>NO ACCESS</h1>"

    # Query all athletes and teams
    athletes = User.query.filter_by(type='athlete').all()
    teams = Team.query.all()

    return render_template('admin_dashboard.html', athletes=athletes, teams=teams, user=current_user)

@routes.route('/team/edit/dashboard')
@login_required
def team_edit_dashboard():

    # Ensure the current user is an admin
    if current_user.type != "admin":
        return "<h1>NO ACCESS</h1>"

    # Query all teams
    teams = Team.query.all()

    return render_template('team_edit_dashboard.html', teams=teams, user=current_user)

@routes.route('/update_position/<int:athlete_id>', methods=['POST'])
@login_required
def update_position(athlete_id):
    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        return jsonify(success=False)

    position = request.json.get('position')

    # Update the athlete's position
    athlete.position = position
    db.session.commit()

    return jsonify(success=True)

@routes.route('/user/edit/dashboard')
@login_required
def user_edit_dashboard():

    # Ensure the current user is an admin
    if current_user.type != "admin":
        return "<h1>NO ACCESS</h1>"

    # Query all users
    users = User.query.all()

    return render_template('user_edit_dashboard.html', users=users, user=current_user)

@routes.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def user_edit(id):
    # Ensure the current user is an admin
    if current_user.type != "admin":
        return "<h1>NO ACCESS</h1>"

    edited_user = User.query.get(id)

    if request.method == 'POST':

        #checks if the admin wants to change the type of user
        if edited_user.type != request.form.get('type'):

            from .models import Admin, Peak, Coach, Athlete

            if request.form.get('type') == "admin":
                u = Admin(colby_id = edited_user.colby_id,
                    first_name = request.form.get('first_name'),
                    last_name = request.form.get('last_name'),
                    password = edited_user.password,
                    email = request.form.get('email')
                    )
                db.session.delete(edited_user)
                db.session.add(u)
                db.session.commit()

            elif request.form.get('type') == "peak":
                u = Peak(colby_id = edited_user.colby_id,
                    first_name = request.form.get('first_name'),
                    last_name = request.form.get('last_name'),
                    password = edited_user.password,
                    email = request.form.get('email')
                    )
                db.session.delete(edited_user)
                db.session.add(u)
                db.session.commit()

            elif request.form.get('type') == "coach":
                u = Coach(colby_id = edited_user.colby_id,
                    first_name = request.form.get('first_name'),
                    last_name = request.form.get('last_name'),
                    password = edited_user.password,
                    email = request.form.get('email')
                    )
                db.session.delete(edited_user)
                db.session.add(u)
                db.session.commit()
            
            elif request.form.get('type') == "athlete":
                u = Athlete(colby_id = edited_user.colby_id,
                    first_name = request.form.get('first_name'),
                    last_name = request.form.get('last_name'),
                    password = edited_user.password,
                    email = request.form.get('email'),
                    gender = request.form.get('gender'),
                    class_year = request.form.get('class_year'),
                    
                    )
                db.session.delete(edited_user)
                db.session.add(u)
                db.session.commit()
            
        else:
            edited_user.first_name = request.form.get('first_name')
            edited_user.last_name = request.form.get('last_name')
            edited_user.email = request.form.get('email')
            if edited_user.type == 'athlete':
                edited_user.gender = request.form.get('gender')
                edited_user.class_year = request.form.get('class_year')
                edited_user.hawkin_api_id = request.form.get('hawkin_api_id')  

            # Save the changes to the database
            db.session.commit()

        return redirect(url_for('main.user_edit_dashboard'))

    return render_template('user_edit.html', edited_user=edited_user, user=current_user)


@routes.route('/team/edit/<int:id>')
@login_required
def team_edit(id):
    # Ensure the current user is an admin
    if current_user.type != "admin":
        return "<h1>NO ACCESS</h1>"

    # Query all athletes and Peak users
    athletes = User.query.filter_by(type='athlete').all()
    peaks = User.query.filter_by(type='peak').all()
    coaches = User.query.filter_by(type='coach').all()
    team = Team.query.get(id)

    def has_athlete(team, athlete):
        return any(association.user == athlete for association in team.team_associations if association.role == 'athlete')

    def has_coach(team, coach):
        return any(association.user == coach for association in team.team_associations if association.role == 'coach')

    def has_peak(team, peak):
        return any(association.user == peak for association in team.team_associations if association.role == 'peak')

    # Example of how to use the has_athlete function
    for athlete in athletes:
        print(athlete)
        print(has_athlete(team, athlete))  # This should print True or False

    return render_template('team_edit.html', athletes=athletes, peaks=peaks, user=current_user, team=team, coaches=coaches, has_athlete=has_athlete, has_coach=has_coach, has_peak=has_peak)


@routes.route('/update_team/<int:team_id>/<int:user_id>', methods=['POST'])
def update_team(team_id, user_id):
    team = Team.query.get(team_id)
    user = User.query.get(user_id)
    membership_data = request.json

    if team and user:
        membership = membership_data.get('membership')
        team_association = TeamUserAssociation.query.filter_by(team_id=team_id, user_id=user_id).first()

        if membership:
            if not team_association:
                new_association = TeamUserAssociation(team=team, user=user, role=user.type)
                db.session.add(new_association)
        else:
            if team_association:
                db.session.delete(team_association)

        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False)

@routes.route('/note/new', methods=['GET', 'POST'])
@login_required
def new_note():

    if request.method == 'GET':
        if current_user.type == "peak":

            peak = Peak.query.filter_by(colby_id=current_user.colby_id).first()
            athletes = []
            for team_association in peak.team_associations:
                if team_association.role == 'peak':
                    team = team_association.team
                    athletes.extend([association.user for association in team.team_associations if association.role == 'athlete'])

            # removing duplicates
            athletes = list(set(athletes))

            # sort athletes by last name
            athletes.sort(key=lambda athlete: athlete.last_name)

            return render_template('create_notes_dashboard.html', athletes=athletes, user=current_user)

        elif current_user.type == "admin":

            athletes = User.query.filter_by(type='athlete').all()
            return render_template('create_notes_dashboard.html', athletes=athletes, user=current_user)
        
        else:
            return "Invalid user type", 400  # Or redirect, render_templat

    if request.method == 'POST':
        print(request.form)
        note_text = request.form.get('note')
        status = request.form.get('status')
        athlete_id = request.form.get('athlete')

        # Find the athlete and user (creator)
        athlete = Athlete.query.get(athlete_id)
        user = User.query.get(current_user.id)

        if athlete and user:
            # Create a new Note
            note = Note(text=note_text, 
                        visible=True, 
                        creator=user, 
                        receiver=athlete)
            
            # Change the athlete's status
            athlete.status = status
            
            # add the note to the database
            db.session.add(note)
            db.session.commit()

            # Add a flash message
            flash('Note created successfully!')

            # Redirect to wherever you want to go after successfully submitting the note
            return redirect(url_for('main.home'))
        else:
            return "Invalid request", 400
            
# notes dasboard page
@routes.route('/note/dashboard', methods=['GET'])
@login_required
def notes_dashboard():

    if current_user.type == "peak":
        # Get all notes created by the peak
        notes = Note.query.filter_by(creator_id=current_user.id).order_by(Note.created_at.desc()).all()

    else:
        notes = Note.query.order_by(Note.created_at.desc()).all()

    # Render the admin dashboard template with the notes
    return render_template('notes_dasboard.html',user=current_user, notes=notes)

@routes.route('/note/edit/<int:note_id>', methods=['POST'])
def update_note_visibility(note_id):

    note = Note.query.get(note_id)
    if note:
        visibility = request.json.get('visibility')
        note.visible = visibility
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False)
    
@routes.route('/user/new', methods=['GET', 'POST'])
@login_required
def new_user():
    # Ensure the current user is an admin
    if current_user.type != "admin":
        return "<h1>NO ACCESS</h1>"
    
    if request.method == 'POST':
        # Extract user information from form
        colby_id = request.form.get('colby_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        gender = request.form.get('gender')
        class_year = request.form.get('class_year')
        user_type = request.form.get('type')
        selected_team_id = request.form.get('team')  # Assuming this is how you get the team ID

        # Create new user
        bol, user = create_user(colby_id, first_name, last_name, email, gender, class_year, user_type)
        if bol:
            db.session.add(user)

            # If a team is selected, add the user to the team
            if selected_team_id:
                team = Team.query.get(selected_team_id)
                if team:
                    team_association = TeamUserAssociation(user=user, team=team, role=user_type)
                    db.session.add(team_association)

            db.session.commit()
            return redirect(url_for('main.user_edit_dashboard'))
        else:
            # Handle error
            print(user)
            return redirect(url_for('main.new_user'))

    # Get teams for the team selection dropdown in the form
    teams = Team.query.all()
    return render_template('user_new.html', user=current_user, teams=teams)


@routes.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Read the file
            df = pd.read_excel(file) if file.filename.endswith('.xlsx') else pd.read_csv(file)
            df['error'] = df.duplicated('Colby ID')

            users = []
            for index, row in df.iterrows():
                #print(f"Processing row: {row}")
                try: 
                    success, user_or_error = create_user(
                        colby_id=row['Colby ID'],
                        first_name=row['Name'],
                        last_name=row['Last Name'],
                        email=row['Email'],
                        gender=row['Gender'],
                        class_year=row['Class Year'],
                        user_type=row['Type of user'],
                        hawkin_api_id=row['Hawkin API ID'],  
                        team_name=row.get('Team')
                    )

                    if success:
                        print('success')
                        db.session.add(user_or_error)
                        db.session.commit()
                        users.append({
                            'colby_id': row['Colby ID'],
                            'name': row['Name'],
                            'last_name': row['Last Name'],
                            'email': row['Email'],
                            'type': row['Type of user'],
                            'team': row['Team'],
                            'gender': row['Gender'],
                            'class_year': row['Class Year'],
                            'status': 'Added'
                        })
                    else:
                        users.append({
                            'colby_id': row['Colby ID'],
                            'name': row['Name'],
                            'last_name': row['Last Name'],
                            'email': row['Email'],
                            'type': row['Type of user'],
                            'team': row['Team'],
                            'gender': row['Gender'],
                            'class_year': row['Class Year'],
                            'status': f'Error: {user_or_error[1]}'
                        })
                
                except IntegrityError as ie:
                    print(f"IntegrityError: {ie}")
                    
                    db.session.rollback()  # Rollback the transaction
                    users.append({
                        'colby_id': row['Colby ID'],
                        'name': row['Name'],
                        'last_name': row['Last Name'],
                        'email': row['Email'],
                        'type': row['Type of user'],
                        'team': row['Team'],
                        'gender': row['Gender'],
                        'class_year': row['Class Year'],
                        'status': 'Duplicate email'
                    })
                
                except Exception as e:
                    print(f"Unexpected error: {e}")


            return render_template('upload.html', users=users, user=current_user)

    return render_template('upload.html', users=None, user=current_user)


@routes.route('/user/remove/<int:id>', methods=['POST'])
@login_required
def remove_user(id):
    # Ensure the current user is an admin
    if current_user.type != "admin":
        return "<h1>NO ACCESS</h1>"

    user = User.query.get(id)

    # Check if the user exists
    if not user:
        return "<h1>User not found</h1>"

    # Remove all associated TeamUserAssociation entries
    associations = TeamUserAssociation.query.filter_by(user_id=id).all()
    for association in associations:
        db.session.delete(association)

    # Remove the user from the database
    db.session.delete(user)
    db.session.commit()

    # Prepare the response JSON
    response = {"success": True}

    return jsonify(response)

@routes.route('/new_team')
@login_required
def new_team():
    # Fetch athletes, coaches, and peak users to pass to the template
    athletes = User.query.filter_by(type='athlete').all()
    coaches = User.query.filter_by(type='coach').all()
    peaks = User.query.filter_by(type='peak').all()

    return render_template('new_team.html', athletes=athletes, coaches=coaches, peaks=peaks, user=current_user)


@routes.route('/create_team', methods=['POST'])
@login_required
def create_team():
    if current_user.type != "admin":
        return "<h1>NO ACCESS</h1>"

    team_name = request.form.get('team_name')

    if not team_name:
        flash('Team name is required.', 'error')
        return redirect(url_for('team_edit'))

    # Create a new team
    new_team = Team(name=team_name)
    db.session.add(new_team)

    # Add selected athletes, coaches, and peak users to the team
    for user_type in ['athlete_ids', 'coach_ids', 'peak_ids']:
        user_ids = request.form.getlist(user_type)
        for user_id in user_ids:
            user = User.query.get(int(user_id))
            if user:
                association = TeamUserAssociation(team=new_team, user=user, role=user.type)
                db.session.add(association)

    db.session.commit()
    flash('Team created successfully.', 'success')
    return redirect(url_for('main.team', id=new_team.id))

@routes.route('/delete_team/<int:team_id>', methods=['POST'])
@login_required
def delete_team(team_id):
    if current_user.type != "admin":
        return jsonify(success=False), 403  # Forbidden access

    team = Team.query.get(team_id)
    if not team:
        return jsonify(success=False), 404  # Team not found

    # Delete all associations related to the team
    TeamUserAssociation.query.filter_by(team_id=team_id).delete()

    # Deleting team
    db.session.delete(team)
    db.session.commit()

    return jsonify(success=True), 200



