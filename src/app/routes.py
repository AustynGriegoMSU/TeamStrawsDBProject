from app import app
import bcrypt
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index() -> str: 
    return render_template('index.html')

# User signup
@app.route('/users/signup', methods=['GET', 'POST'])
def signup() -> str:
    form: SignUpForm = SignUpForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user: User = db.session.query(User).filter_by(id=form.id.data).first()
        if existing_user:
            form.id.errors.append('User ID already exists. Please choose a different ID.')
        # Check that passwords match, if not returns message
        elif form.passwd.data != form.passwd_confirm.data:
            form.passwd_confirm.errors.append('Passwords do not match.')
        # If no errors, create the user
        else:
            # Salt/Hash password
            salt: bytes = bcrypt.gensalt()
            hashed: bytes = bcrypt.hashpw(form.passwd.data.encode('utf-8'), salt)
            user: User = User(
                id=form.id.data,
                name=form.name.data,
                about=form.about.data,
                passwd=hashed
            )
            db.session.add(user)
            db.session.commit()
            # Flash a success message to let user know account was created
            flash('Account created, please log in.')
            # Redirect to login after successful signup
            return redirect(url_for('login'))
    return render_template('signup.html', form=form)

# User login
@app.route('/users/login', methods=['GET', 'POST'])
def login() -> str:
    form: LoginForm = LoginForm()
    if form.validate_on_submit():
        # Check for user in database
        user: User = db.session.query(User).filter_by(id=form.id.data).first()
        # If user exists and password is correct (checked with bcrypt), log the user in
        if user and bcrypt.checkpw(form.passwd.data.encode('utf-8'), user.passwd):
            login_user(user)
            # Upon successful login, flash success message
            flash('Logged in successfully.')
            # Upon successful login, redirect to the schools list page
            return redirect(url_for('list_schools'))
        # If user doesn't exist or password is incorrect, show error message
        else:
            form.id.errors.append('Invalid user ID or password.')
    return render_template('login.html', form=form)

# User logout Added 10/02/2025 AG#
#To see the logout button, user must be logged in
@login_required
@app.route('/users/signout', methods=['GET', 'POST'])
def signout() -> Response:
    """
    Log out the current user and redirect to login page.
    
    Returns:
        Response: Redirect to login page
    """
    logout_user()
    # Flash a message to let user know they have been signed out
    flash('You have been signed out.')
    # Redirect to login page after logout
    return redirect(url_for('login'))