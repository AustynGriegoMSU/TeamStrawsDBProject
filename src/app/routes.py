from src.app import app, con, cur
import bcrypt
from flask import render_template, redirect, url_for, flash, Response
from flask_login import login_user, logout_user, login_required
from src.app.models import User
from src.app.forms import SignUpForm, LoginForm


def password_matches(submitted_password: str, stored_password) -> bool:
    if stored_password is None:
        return False

    stored_text = stored_password.decode('utf-8') if isinstance(stored_password, bytes) else str(stored_password)
    if stored_text.startswith('$2'):
        return bcrypt.checkpw(submitted_password.encode('utf-8'), stored_text.encode('utf-8'))
    return submitted_password == stored_text

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
        customer_row = cur.execute(
            'SELECT "Customer ID" FROM Customer WHERE "Username" = ?',
            (form.username.data,)
        ).fetchone()
        employee_row = cur.execute(
            'SELECT "Employee ID" FROM Employee WHERE "Username" = ?',
            (form.username.data,)
        ).fetchone()
        if customer_row or employee_row:
            form.username.errors.append('Username already exists. Please choose a different username.')
        elif form.role.data == 'customer' and not form.ssn.data:
            form.ssn.errors.append('SSN is required for customer signup.')
        elif form.role.data == 'employee' and form.branch_id.data is None:
            form.branch_id.errors.append('Branch ID is required for employee signup.')
        elif form.passwd.data != form.passwd_confirm.data:
            form.passwd_confirm.errors.append('Passwords do not match.')
        else:
            hashed = bcrypt.hashpw(form.passwd.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            if form.role.data == 'customer':
                cur.execute(
                    'INSERT INTO Customer ("First Name", "Last Name", "Address", "Phone #", "Username", "Password", "SSN") VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (
                        form.first_name.data,
                        form.last_name.data or None,
                        form.address.data or None,
                        form.phone.data,
                        form.username.data,
                        hashed,
                        int(form.ssn.data),
                    )
                )
            else:
                cur.execute(
                    'INSERT INTO Employee ("Branch ID", "First Name", "Last Name", "Username", "Password") VALUES (?, ?, ?, ?, ?)',
                    (
                        form.branch_id.data,
                        form.first_name.data,
                        form.last_name.data or '',
                        form.username.data,
                        hashed,
                    )
                )
            con.commit()
            con.sync()
            flash('Account created, please log in.')
            return redirect(url_for('login'))
    return render_template('signup.html', form=form)

# User login
@app.route('/users/login', methods=['GET', 'POST'])
def login() -> str:
    form: LoginForm = LoginForm()
    if form.validate_on_submit():
        if form.role.data == 'customer':
            row = cur.execute(
                'SELECT "Customer ID", "First Name", "Last Name", "Username", "Password" FROM Customer WHERE "Username" = ?',
                (form.username.data,)
            ).fetchone()
        else:
            row = cur.execute(
                'SELECT "Employee ID", "First Name", "Last Name", "Username", "Password" FROM Employee WHERE "Username" = ?',
                (form.username.data,)
            ).fetchone()

        if row and password_matches(form.passwd.data, row[4]):
            user = User(
                role=form.role.data,
                record_id=row[0],
                username=row[3],
                first_name=row[1],
                last_name=row[2],
            )
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('index'))
        else:
            form.username.errors.append('Invalid username or password.')
    return render_template('login.html', form=form)

# User logout
@app.route('/users/signout', methods=['GET', 'POST'])
@login_required
def signout() -> Response:
    logout_user()
    flash('You have been signed out.')
    return redirect(url_for('login'))