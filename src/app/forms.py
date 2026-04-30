from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, IntegerField, SelectField, FloatField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class SignUpForm(FlaskForm):
    role = SelectField('User Type', choices=[('customer', 'Customer'), ('employee', 'Employee')], validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[Optional()])
    branch_id = IntegerField('Branch ID', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional()])
    phone = IntegerField('Phone Number', validators=[Optional()])
    username = StringField('Username', validators=[DataRequired()])
    ssn = StringField('SSN', validators=[Optional(), Length(min=9, max=9, message='SSN must be 9 digits.')])
    passwd = PasswordField('Password', validators=[DataRequired(), Length(min=8, message='Password must be at least 8 characters.')])
    passwd_confirm = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Confirm')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    passwd = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Confirm')

class TransferForm(FlaskForm):
    source_account_id = IntegerField(validators=[DataRequired()])
    recipient_account_id = IntegerField('Recipient Account Number', validators=[DataRequired()])
    amount = FloatField('Transfer Amount', validators=[DataRequired(), NumberRange(min=0.01, message='Amount must be greater than 0.')])
    submit_transfer = SubmitField('Send Transfer')

class AccountNicknameForm(FlaskForm):
    account_id = HiddenField(validators=[DataRequired()])
    nickname = StringField('Account Nickname', validators=[Optional(), Length(max=40, message='Nickname must be 40 characters or fewer.')])
    submit_nickname = SubmitField('Save Nickname')

class NewAccountRequestForm(FlaskForm):
    requested_type = SelectField(
        'Requested Account Type',
        choices=[('Checking', 'Checking'), ('Savings', 'Savings')],
        validators=[DataRequired()],
    )
    submit_request = SubmitField('Request New Account')

class ReviewAccountRequestForm(FlaskForm):
    request_id = HiddenField(validators=[DataRequired()])
    action = HiddenField(validators=[DataRequired()])
    submit_review = SubmitField('Submit Review')

class EmployeeTransactionForm(FlaskForm):
    account_id = HiddenField(validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01, message='Amount must be greater than 0.')])
    action = HiddenField(validators=[DataRequired()])
    submit_transaction = SubmitField('Submit')
