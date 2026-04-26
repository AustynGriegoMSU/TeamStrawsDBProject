from flask import Flask
from flask_login import LoginManager
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
app.config['SESSION_PERMANENT'] = False

## Database setup
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
data_dir = os.path.join(project_root, 'data')
os.makedirs(data_dir, exist_ok=True)
local_db_path = os.path.join(data_dir, 'bank.db')

import libsql_experimental as libsql
con = libsql.connect(
    local_db_path,
    sync_url=os.environ.get('TURSO_URL'),
    auth_token=os.environ.get('TURSO_AUTH_TOKEN')
)
con.sync()
cur = con.cursor()

# flask-login setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from src.app.models import User
    try:
        role, record_id = user_id.split(':', 1)
    except ValueError:
        return None

    if role == 'customer':
        row = cur.execute(
            'SELECT "Customer ID", "First Name", "Last Name", "Username" FROM Customer WHERE "Customer ID" = ?',
            (record_id,)
        ).fetchone()
        if row:
            return User(role='customer', record_id=row[0], username=row[3], first_name=row[1], last_name=row[2])

    if role == 'employee':
        row = cur.execute(
            'SELECT "Employee ID", "First Name", "Last Name", "Username" FROM Employee WHERE "Employee ID" = ?',
            (record_id,)
        ).fetchone()
        if row:
            return User(role='employee', record_id=row[0], username=row[3], first_name=row[1], last_name=row[2])

    return None

from src.app import routes
