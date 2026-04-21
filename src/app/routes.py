from src.app import app, con, cur
import bcrypt
from flask import render_template, redirect, url_for, flash, Response, request
from flask_login import login_user, logout_user, login_required, current_user
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

@app.route('/customer/home')
@login_required
def customer_home() -> str:
    if getattr(current_user, 'role', None) != 'customer':
        flash('Customer access only.')
        return redirect(url_for('index'))

    customer_id = current_user.record_id
    accounts = cur.execute(
        '''
        SELECT a."Account ID", a."Account Type", a."Balance", b."Name"
        FROM Account a
        LEFT JOIN Branch b ON b."Branch ID" = a."Branch ID"
        WHERE a."Customer ID" = ?
        ORDER BY a."Account ID" ASC
        ''',
        (customer_id,)
    ).fetchall()

    selected_account_id = request.args.get('account_id', type=int)
    selected_account = None
    transactions = []

    if accounts:
        if selected_account_id is None:
            selected_account_id = accounts[0][0]

        for account in accounts:
            if account[0] == selected_account_id:
                selected_account = account
                break

        if selected_account is None:
            flash('That account is not available for your profile.')
            selected_account_id = accounts[0][0]
            selected_account = accounts[0]

        transactions = cur.execute(
            '''
            SELECT "Transaction ID", "Transaction Type", "Amount", "Time"
            FROM "Transaction"
            WHERE "Account ID" = ?
            ORDER BY "Transaction ID" DESC
            LIMIT 25
            ''',
            (selected_account_id,)
        ).fetchall()

    return render_template(
        'customer_home.html',
        accounts=accounts,
        selected_account=selected_account,
        transactions=transactions,
    )

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
        customer_row = cur.execute(
            'SELECT "Customer ID", "First Name", "Last Name", "Username", "Password" FROM Customer WHERE "Username" = ?',
            (form.username.data,)
        ).fetchone()
        employee_row = cur.execute(
            'SELECT "Employee ID", "First Name", "Last Name", "Username", "Password" FROM Employee WHERE "Username" = ?',
            (form.username.data,)
        ).fetchone()

        role = None
        row = None
        if customer_row and employee_row:
            form.username.errors.append('Username is duplicated across user types. Please contact support.')
            return render_template('login.html', form=form)
        if customer_row:
            role = 'customer'
            row = customer_row
        elif employee_row:
            role = 'employee'
            row = employee_row

        if row and password_matches(form.passwd.data, row[4]):
            user = User(
                role=role,
                record_id=row[0],
                username=row[3],
                first_name=row[1],
                last_name=row[2],
            )
            login_user(user)
            flash('Logged in successfully.')
            if role == 'customer':
                return redirect(url_for('customer_home'))
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