from flask import Flask
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-secret-key'

import libsql_experimental as libsql
con = libsql.connect("bank.db")
cur = con.cursor()

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    row = cur.execute(
        "SELECT id, name, about, passwd FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row:
        return User(id=row[0], name=row[1], about=row[2], passwd=row[3])
    return None

from app import routes
