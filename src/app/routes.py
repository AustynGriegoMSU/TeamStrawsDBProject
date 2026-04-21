from src.app import app, con, cur
import bcrypt
from datetime import datetime
from flask import render_template, redirect, url_for, flash, Response, request
from flask_login import login_user, logout_user, login_required, current_user
from src.app.models import User
from src.app.forms import SignUpForm, LoginForm, TransferForm, AccountNicknameForm, NewAccountRequestForm, ReviewAccountRequestForm


def password_matches(submitted_password: str, stored_password) -> bool:
    if stored_password is None:
        return False

    stored_text = stored_password.decode('utf-8') if isinstance(stored_password, bytes) else str(stored_password)
    if stored_text.startswith('$2'):
        return bcrypt.checkpw(submitted_password.encode('utf-8'), stored_text.encode('utf-8'))
    return submitted_password == stored_text


def ensure_account_request_table() -> None:
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS AccountRequest (
            "Request ID" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Customer ID" INTEGER NOT NULL,
            "Requested Type" TEXT NOT NULL,
            "Status" TEXT NOT NULL DEFAULT 'pending',
            "Requested At" TEXT NOT NULL,
            "Reviewed At" TEXT,
            "Reviewed By Employee ID" INTEGER,
            "Notes" TEXT
        )
        '''
    )
    con.commit()
    con.sync()


def ensure_transaction_details_column() -> None:
    transaction_columns = {
        row[1]
        for row in cur.execute('PRAGMA table_info("Transaction")').fetchall()
    }

    if 'Details' not in transaction_columns:
        cur.execute('ALTER TABLE "Transaction" ADD COLUMN "Details" TEXT')
        con.commit()
        con.sync()


def ensure_account_nickname_column() -> None:
    account_columns = {
        row[1]
        for row in cur.execute('PRAGMA table_info("Account")').fetchall()
    }

    if 'Nickname' not in account_columns:
        cur.execute('ALTER TABLE "Account" ADD COLUMN "Nickname" TEXT')
        con.commit()
        con.sync()


ensure_account_request_table()
ensure_transaction_details_column()
ensure_account_nickname_column()

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index() -> str:
    return render_template('index.html')

@app.route('/customer/home', methods=['GET', 'POST'])
@login_required
def customer_home() -> str:
    if getattr(current_user, 'role', None) != 'customer':
        flash('Customer access only.')
        return redirect(url_for('index'))

    customer_id = current_user.record_id
    transfer_form: TransferForm = TransferForm()
    nickname_form: AccountNicknameForm = AccountNicknameForm()
    new_account_form: NewAccountRequestForm = NewAccountRequestForm()

    account_rows = cur.execute(
        '''
        SELECT a."Account ID", a."Account Type", a."BalanceCents", b."Name", a."Nickname"
        FROM Account a
        LEFT JOIN Branch b ON b."Branch ID" = a."Branch ID"
        WHERE a."Customer ID" = ?
        ORDER BY
            CASE lower(a."Account Type")
                WHEN 'checking' THEN 0
                WHEN 'savings' THEN 1
                ELSE 2
            END,
            a."Account ID" ASC
        ''',
        (customer_id,)
    ).fetchall()

    accounts = [
        {
            'id': row[0],
            'account_type': row[1],
            'balance_cents': int(row[2] or 0),
            'balance': (int(row[2] or 0) / 100),
            'branch_name': row[3],
            'nickname': row[4],
        }
        for row in account_rows
    ]
    checking_accounts = [account for account in accounts if str(account['account_type']).lower() == 'checking']
    savings_accounts = [account for account in accounts if str(account['account_type']).lower() == 'savings']
    other_accounts = [
        account for account in accounts if str(account['account_type']).lower() not in {'checking', 'savings'}
    ]

    selected_account_id = request.args.get('account_id', type=int)

    def posted_account_id() -> int | None:
        values = request.form.getlist('account_id')
        for raw in reversed(values):
            text = (raw or '').strip()
            if text.isdigit():
                return int(text)
        return None

    if request.method == 'POST' and 'submit_transfer' in request.form:
        selected_account_id = request.form.get('source_account_id', type=int) or selected_account_id
    elif request.method == 'POST' and 'submit_nickname' in request.form:
        selected_account_id = posted_account_id() or selected_account_id

    selected_account = None
    transfer_source_account = None
    transactions = []

    account_requests = cur.execute(
        '''
        SELECT "Request ID", "Requested Type", "Status", "Requested At", "Reviewed At", "Notes"
        FROM AccountRequest
        WHERE "Customer ID" = ?
        ORDER BY "Request ID" DESC
        LIMIT 25
        ''',
        (customer_id,)
    ).fetchall()

    account_requests = [
        {
            'id': row[0],
            'requested_type': row[1],
            'status': row[2],
            'requested_at': row[3],
            'reviewed_at': row[4],
            'notes': row[5],
        }
        for row in account_requests
    ]

    if request.method == 'POST' and 'submit_request' in request.form:
        if new_account_form.validate():
            existing_pending = cur.execute(
                '''
                SELECT "Request ID"
                FROM AccountRequest
                WHERE "Customer ID" = ? AND lower("Requested Type") = lower(?) AND "Status" = 'pending'
                LIMIT 1
                ''',
                (customer_id, new_account_form.requested_type.data)
            ).fetchone()

            if existing_pending:
                flash('You already have a pending request for that account type.')
            else:
                cur.execute(
                    'INSERT INTO AccountRequest ("Customer ID", "Requested Type", "Status", "Requested At") VALUES (?, ?, ?, ?)',
                    (
                        customer_id,
                        new_account_form.requested_type.data,
                        'pending',
                        datetime.utcnow().isoformat(timespec='seconds'),
                    )
                )
                con.commit()
                con.sync()
                flash('Account request submitted. An employee must approve it.')
                return redirect(url_for('customer_home'))

    if request.method == 'POST' and 'submit_nickname' in request.form:
        submitted_account_id = posted_account_id()

        if not submitted_account_id:
            flash('Could not update nickname for that account.')
            return redirect(url_for('customer_home'))
        if not nickname_form.validate():
            selected_account_id = submitted_account_id
        else:
            account_owner = cur.execute(
                'SELECT 1 FROM Account WHERE "Account ID" = ? AND "Customer ID" = ? LIMIT 1',
                (submitted_account_id, customer_id)
            ).fetchone()

            if not account_owner:
                flash('That account is not available for editing.')
                return redirect(url_for('customer_home'))

            nickname_value = (nickname_form.nickname.data or '').strip()
            cur.execute(
                'UPDATE Account SET "Nickname" = ? WHERE "Account ID" = ? AND "Customer ID" = ?',
                (nickname_value or None, submitted_account_id, customer_id)
            )
            con.commit()
            con.sync()
            flash('Account nickname updated.')
            return redirect(url_for('customer_home', account_id=submitted_account_id))

    if accounts:
        account_lookup = {account['id']: account for account in accounts}

        if selected_account_id is not None:
            for account in accounts:
                if account['id'] == selected_account_id:
                    selected_account = account
                    break

            if selected_account is None:
                flash('That account is not available for your profile.')

        if selected_account is not None:
            nickname_form.account_id.data = selected_account['id']

        if not transfer_form.source_account_id.data:
            transfer_form.source_account_id.data = selected_account['id'] if selected_account else accounts[0]['id']

        transfer_source_id = int(transfer_form.source_account_id.data or 0)
        transfer_source_account = account_lookup.get(transfer_source_id) or accounts[0]

        if request.method == 'POST' and 'submit_transfer' in request.form and transfer_form.validate():
            source_account_id = int(transfer_form.source_account_id.data or 0)
            source_account = account_lookup.get(source_account_id)
            recipient_account = cur.execute(
                '''
                SELECT "Account ID", "BalanceCents"
                FROM Account
                WHERE "Account ID" = ?
                ''',
                (transfer_form.recipient_account_id.data,)
            ).fetchone()

            source_balance_cents = int(source_account['balance_cents'] or 0) if source_account else 0
            transfer_amount = float(transfer_form.amount.data or 0)
            transfer_amount_cents = int(round(transfer_amount * 100))

            if transfer_amount <= 0:
                transfer_form.amount.errors.append('Transfer amount must be greater than 0.')
            elif not source_account:
                transfer_form.source_account_id.errors.append('Source account not found.')
            elif not recipient_account:
                transfer_form.recipient_account_id.errors.append('Recipient account not found.')
            elif recipient_account[0] == source_account['id']:
                transfer_form.recipient_account_id.errors.append('Cannot transfer to the same account.')
            elif transfer_amount_cents > source_balance_cents:
                transfer_form.amount.errors.append('Insufficient funds for this transfer.')
            else:
                source_after_cents = source_balance_cents - transfer_amount_cents
                recipient_before_cents = int(recipient_account[1] or 0)
                recipient_after_cents = recipient_before_cents + transfer_amount_cents
                now = datetime.utcnow().isoformat(timespec='seconds')
                source_details = f'Transfer to account #{recipient_account[0]}'
                recipient_details = f'Transfer from account #{source_account["id"]}'

                cur.execute(
                    'UPDATE Account SET "BalanceCents" = ? WHERE "Account ID" = ?',
                    (source_after_cents, source_account['id'])
                )
                cur.execute(
                    'UPDATE Account SET "BalanceCents" = ? WHERE "Account ID" = ?',
                    (recipient_after_cents, recipient_account[0])
                )

                cur.execute(
                    'INSERT INTO "Transaction" ("Account ID", "Transaction Type", "AmountCents", "Time", "Details") VALUES (?, ?, ?, ?, ?)',
                    (source_account['id'], 'transfer', transfer_amount_cents, now, source_details)
                )
                cur.execute(
                    'INSERT INTO "Transaction" ("Account ID", "Transaction Type", "AmountCents", "Time", "Details") VALUES (?, ?, ?, ?, ?)',
                    (recipient_account[0], 'deposit', transfer_amount_cents, now, recipient_details)
                )

                con.commit()
                con.sync()
                flash('Transfer completed successfully.')
                return redirect(url_for('customer_home', account_id=source_account['id']))

        if selected_account is not None:
            transactions = cur.execute(
                '''
                SELECT "Transaction ID", "Transaction Type", "AmountCents", "Time", "Details"
                FROM "Transaction"
                WHERE "Account ID" = ?
                ORDER BY "Transaction ID" DESC
                LIMIT 25
                ''',
                (selected_account_id,)
            ).fetchall()

            transactions = [
                {
                    'id': row[0],
                    'transaction_type': row[1],
                    'amount_cents': int(row[2] or 0),
                    'amount': (int(row[2] or 0) / 100),
                    'time': row[3],
                    'details': row[4],
                }
                for row in transactions
            ]

    return render_template(
        'customer_home.html',
        accounts=accounts,
        checking_accounts=checking_accounts,
        savings_accounts=savings_accounts,
        other_accounts=other_accounts,
        selected_account=selected_account,
        transfer_source_account=transfer_source_account,
        transactions=transactions,
        transfer_form=transfer_form,
        nickname_form=nickname_form,
        new_account_form=new_account_form,
        account_requests=account_requests,
    )


@app.route('/employee/home', methods=['GET', 'POST'])
@login_required
def employee_home() -> str:
    if getattr(current_user, 'role', None) != 'employee':
        flash('Employee access only.')
        return redirect(url_for('index'))

    review_form: ReviewAccountRequestForm = ReviewAccountRequestForm()

    if request.method == 'POST':
        if not review_form.validate():
            flash('Could not process review action. Please try again.')
            return redirect(url_for('employee_home'))

        request_id = int(review_form.request_id.data)
        action = review_form.action.data.lower().strip()

        request_row = cur.execute(
            'SELECT "Request ID", "Customer ID", "Requested Type", "Status" FROM AccountRequest WHERE "Request ID" = ?',
            (request_id,)
        ).fetchone()

        if not request_row:
            flash('Request not found.')
        elif str(request_row[3]).lower() != 'pending':
            flash('That request was already reviewed.')
        else:
            employee_branch_row = cur.execute(
                'SELECT "Branch ID" FROM Employee WHERE "Employee ID" = ?',
                (current_user.record_id,)
            ).fetchone()

            if not employee_branch_row:
                flash('Employee branch not found; cannot review request.')
            elif action == 'approve':
                cur.execute(
                    'INSERT INTO Account ("Customer ID", "Branch ID", "BalanceCents", "Account Type") VALUES (?, ?, ?, ?)',
                    (
                        request_row[1],
                        employee_branch_row[0],
                        0,
                        request_row[2],
                    )
                )
                new_account_id = cur.execute('SELECT last_insert_rowid()').fetchone()[0]
                cur.execute(
                    'UPDATE AccountRequest SET "Status" = ?, "Reviewed At" = ?, "Reviewed By Employee ID" = ?, "Notes" = ? WHERE "Request ID" = ?',
                    (
                        'approved',
                        datetime.utcnow().isoformat(timespec='seconds'),
                        current_user.record_id,
                        f'Created account #{new_account_id}',
                        request_id,
                    )
                )
                con.commit()
                con.sync()
                flash(f'Request approved. New account #{new_account_id} created.')
            elif action == 'reject':
                cur.execute(
                    'UPDATE AccountRequest SET "Status" = ?, "Reviewed At" = ?, "Reviewed By Employee ID" = ?, "Notes" = ? WHERE "Request ID" = ?',
                    (
                        'rejected',
                        datetime.utcnow().isoformat(timespec='seconds'),
                        current_user.record_id,
                        'Rejected by employee',
                        request_id,
                    )
                )
                con.commit()
                con.sync()
                flash('Request rejected.')
            else:
                flash('Invalid action.')

        return redirect(url_for('employee_home'))

    requests = cur.execute(
        '''
        SELECT ar."Request ID", ar."Customer ID", c."Username", ar."Requested Type", ar."Status", ar."Requested At", ar."Reviewed At", ar."Notes"
        FROM AccountRequest ar
        JOIN Customer c ON c."Customer ID" = ar."Customer ID"
        ORDER BY ar."Request ID" DESC
        LIMIT 50
        '''
    ).fetchall()

    requests = [
        {
            'id': row[0],
            'customer_id': row[1],
            'username': row[2],
            'requested_type': row[3],
            'status': row[4],
            'requested_at': row[5],
            'reviewed_at': row[6],
            'notes': row[7],
        }
        for row in requests
    ]

    return render_template('employee_home.html', requests=requests, review_form=review_form)

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
        elif form.role.data == 'employee' and not cur.execute(
            'SELECT "Branch ID" FROM Branch WHERE "Branch ID" = ?',
            (form.branch_id.data,)
        ).fetchone():
            form.branch_id.errors.append('Branch ID does not exist. Enter a valid branch ID.')
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
            return redirect(url_for('employee_home'))
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