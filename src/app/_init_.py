from flask import Flask

app = Flask(__name__)

#connect TursoDB
import turso

con = turso.connect("bank.db")
cur = con.cursor()
