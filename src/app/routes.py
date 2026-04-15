from src.app import app, con, cur
import bcrypt
from flask import render_template, redirect, url_for, flash, Response
from flask_login import login_user, logout_user, login_required
from src.app.models import User
from src.app.forms import SignUpForm, LoginForm

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
        row = cur.execute("SELECT id FROM users WHERE id = ?", (form.id.data,)).fetchone()
        if row:
            form.id.errors.append('User ID already exists. Please choose a different ID.')
        elif form.passwd.data != form.passwd_confirm.data:
            form.passwd_confirm.errors.append('Passwords do not match.')
        else:
            salt: bytes = bcrypt.gensalt()
            hashed: bytes = bcrypt.hashpw(form.passwd.data.encode('utf-8'), salt)
            cur.execute(
                "INSERT INTO users (id, name, about, passwd) VALUES (?, ?, ?, ?)",
                (form.id.data, form.name.data, form.about.data, hashed)
            )
            con.commit()
            flash('Account created, please log in.')
            return redirect(url_for('login'))
    return render_template('signup.html', form=form)

# User login
@app.route('/users/login', methods=['GET', 'POST'])
def login() -> str:
    form: LoginForm = LoginForm()
    if form.validate_on_submit():
        row = cur.execute(
            "SELECT id, name, about, passwd FROM users WHERE id = ?", (form.id.data,)
        ).fetchone()
        if row and bcrypt.checkpw(form.passwd.data.encode('utf-8'), row[3]):
            user: User = User(id=row[0], name=row[1], about=row[2], passwd=row[3])
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('index'))
        else:
            form.id.errors.append('Invalid user ID or password.')
    return render_template('login.html', form=form)

# User logout
@app.route('/users/signout', methods=['GET', 'POST'])
@login_required
def signout() -> Response:
    logout_user()
    flash('You have been signed out.')
    return redirect(url_for('login'))