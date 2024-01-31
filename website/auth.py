"""
Jonathan Sosa 
auth.py
may-jun 2023
"""

# routes on the file (you can look these up and it will take you there)
## login --> handles the login for the page
## logout --> logout the user

# imoprts
from flask import Blueprint, request, redirect, url_for, render_template
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from .models import User, Team, Coach, Peak

# flask blueprint for routes
auth = Blueprint('auth', __name__)

# auth routes
@auth.route('/login', methods = ['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        colby_id = request.form.get('colby_id')
        password = request.form.get('password')

        print(colby_id)
        print(password)

        user = User.query.filter_by(colby_id=colby_id).first()

        if not user or not check_password_hash(user.password, password):
            return render_template("login.html", user=current_user, athlete=current_user)

        login_user(user, remember = True)

        return redirect(url_for('main.home'))
    
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
