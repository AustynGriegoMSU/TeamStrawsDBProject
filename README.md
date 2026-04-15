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
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
 
Create a file named ".env" and paste following in file:
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