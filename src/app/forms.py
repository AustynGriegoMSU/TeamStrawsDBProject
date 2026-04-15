from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Optional

class SignUpForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional()])
    phone = IntegerField('Phone Number', validators=[Optional()])
    username = StringField('Username', validators=[DataRequired()])
    ssn = IntegerField('SSN', validators=[DataRequired()])
    passwd = PasswordField('Password', validators=[DataRequired(), Length(min=8, message='Password must be at least 8 characters.')])
    passwd_confirm = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Confirm')

class LoginForm(FlaskForm):
    role = SelectField('User Type', choices=[('customer', 'Customer'), ('employee', 'Employee')], validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    passwd = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Confirm')
