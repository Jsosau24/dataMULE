'''
This page contains all the routes, related to signin, logout, password reset
'''

# imoprts
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from .models import User, Team, Coach, Peak
from .email import *
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash
from . import db
from dotenv import load_dotenv
import os

# flask blueprint for routes
auth = Blueprint('auth', __name__)

# auth routes
@auth.route('/login', methods = ['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        colby_id = request.form.get('colby_id')
        password = request.form.get('password')

        user = User.query.filter_by(colby_id=colby_id).first()

        if not user or not check_password_hash(user.password, password):
            return render_template("login.html", user=current_user, athlete=current_user)

        login_user(user, remember = True)

        return redirect(url_for('main.home'))
    
    return render_template('login.html')

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Serializer for decoding the token
    load_dotenv()

    s = URLSafeTimedSerializer(os.getenv('secret_key'))

    try:
        # Attempt to decode the token
        # Note: Adjust max_age to the desired expiration time of the token
        email = s.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=3600)
    except SignatureExpired:
        # Token has expired
        flash('The password reset link is expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    except BadSignature:
        # Token is invalid
        flash('Invalid password reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:
            flash("Passwords do not match.", "warning")
            return redirect(url_for('auth.reset_password', token=token))

        user = User.query.filter_by(email=email).first()
        if user:
            # Update user's password
            user.password = generate_password_hash(password)
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('User not found.', 'danger')

    # Render the reset password form if GET request or error
    return render_template('reset_password.html', token=token)

@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('colby_id')
        user = User.query.filter_by(colby_id=email).first()
        if user:
            send_password_reset_email(user.email)
            flash('Please check your email for a password reset link.', 'info')
        else:
            flash('No account found with that email.', 'warning')
    return render_template('forgot_password.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
