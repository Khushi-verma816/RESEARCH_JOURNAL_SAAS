from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User

class RegisterForm(FlaskForm):
    """Form for user registration"""

    first_name = StringField('First Name',
                              validators=[DataRequired(), Length(min=2, max=100)])

    last_name = StringField('Last Name',
                             validators=[DataRequired(), Length(min=2, max=100)])

    email = StringField('Email Address',
                         validators=[DataRequired(), Email()])

    password = PasswordField('Password',
                              validators=[DataRequired(), Length(min=8)])

    confirm_password = PasswordField('Confirm Password',
                                      validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Create Account')

    def validate_email(self, email):
        """Check if email is already taken"""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('This email is already registered. Please login instead.')

class LoginForm(FlaskForm):
    """Form for user login"""

    email = StringField('Email Address',
                         validators=[DataRequired(), Email()])

    password = PasswordField('Password',
                              validators=[DataRequired()])

    remember_me = BooleanField('Remember Me')

    submit = SubmitField('Login')

class ForgotPasswordForm(FlaskForm):
    """Form for requesting password reset"""

    email = StringField('Email Address',
                         validators=[DataRequired(), Email()])

    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    """Form for resetting password"""

    password = PasswordField('New Password',
                              validators=[DataRequired(), Length(min=8)])

    confirm_password = PasswordField('Confirm New Password',
                                      validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Reset Password')
