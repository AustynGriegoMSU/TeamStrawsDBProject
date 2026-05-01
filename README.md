# Team Straws Database Project

## Team Members: 
Austyn Griego, Riley Blank, Eric Do

## Course:
CS3810 Principles of Database Systems

## Due Date:
May 14th, 2026

## Description
A simple banking application to demonstrate usage/structure of a database system. The requirements for application called for an ERD chart, a working DB Schema, a minimal UI, and a powerpoint presentation to share our project. 

## Application Setup 

### On macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### On Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
 
Create a file named ".env" in the project root directory and paste the following:
```
TURSO_URL=libsql://bank-3810bankproject.aws-us-west-2.turso.io
TURSO_AUTH_TOKEN=<get from team OR follow startup guide on Turso>
SECRET_KEY=change-this-secret-key
```
 
Run the app from terminal with:
```bash
python run.py
```
On browser launch the following:
```
http://127.0.0.1:5000 
```

## Troubleshooting
**Missing .env file:**
- The app will crash if `.env` is missing or incomplete. Make sure it's in the project root
- Verify all three variables are set: `TURSO_URL`, `TURSO_AUTH_TOKEN`, and `SECRET_KEY`

**Port already in use:**
- If port 5000 is already in use, modify `run.py` to use a different port: `app.run(debug=True, port=5001)`