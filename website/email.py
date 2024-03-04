from flask_mail import Mail, Message
from flask import current_app, url_for
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

# Initialize the Flask-Mail extension somewhere in your application setup
mail = Mail()

def send_password_reset_email(user_email):
    token = generate_confirmation_token(user_email)
    msg = Message("Password Reset Request",
                  sender="data.mule2024@outlook.com",  # Match MAIL_USERNAME
                  recipients=[user_email])
    msg.body = f'''To reset your password, visit the following link:
    {url_for('auth.reset_password', token=token, _external=True)}
    If you did not make this request, please ignore this email and no changes will be made.
    '''
    mail.send(msg)

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email

