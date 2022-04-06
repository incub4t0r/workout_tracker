#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, session, send_from_directory, make_response
import sqlite3, os, hashlib

db = "storage.db"

app = Flask(__name__)

file_location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def hash(data):
    return hashlib.sha224(data.replace('\n', '').encode('ascii')).hexdigest()

def createTable():
    adminpass = hash("supersecret")
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("drop table if exists users")
    c.execute(
        "create table if not exists users(username string, password string) ")
    c.execute(
        "insert into users (username, password) values ('admin','" + (adminpass) + "')")
    conn.commit()
@app.route('/', methods=['GET'])
def welcome():
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return render_template('login.html', error="username or password cannot be empty!")
        hashpass = hash(password)
        try:
            conn = sqlite3.connect('storage.db')
            c = conn.cursor()
            # https://docs.python.org/3/library/sqlite3.html
            c.execute("SELECT * FROM users WHERE username=:username AND password=:password", 
                        {"username": username, "password":hashpass})
            rval = c.fetchone()
            if rval:
                session['username'] = rval
                return redirect("/home", 303)
            else:
                return redirect("/login", 303)
        except:
            return render_template('login.html', error="error logging in, contact admin.")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return render_template('register.html', error="username or password cannot be empty!")
        hashpass = hash(password)
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=:username",{"username": username})
            rval = c.fetchone()
            if rval:
                return render_template("register.html", error="Username already exists")
                # print("username exists")
            # else:
            #     print("username does not exist")
            c.execute("insert into users (username, password) values (:username, :password)", 
                        {"username": username, "password":hashpass})
            conn.commit()
        except:
            return render_template('register.html', error="error creating a new user, contact admin.")
        return redirect('/home')

@app.route('/home', methods=['GET'])
def main():
    if not 'username' in session:
        return redirect("/login", 303)
    return render_template('main.html', name=session['username'][0])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect("/", 303)

if __name__ == '__main__':
    try:
        os.remove(db)
    except OSError:
        pass
    with open(os.path.join(file_location, "secrets.txt"), 'r') as f:
        s = f.readlines()
    app.secret_key = s[0].replace('\n', '')
    app.config.update(SESSION_COOKIE_HTTPONLY=False)
    createTable()
    # app.run(host="localhost", debug=True)
    app.run(host="10.211.166.189")
