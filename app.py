#!/usr/bin/env python3

from typing import OrderedDict
from flask import Flask, render_template, request, redirect, session, send_from_directory, make_response
import sqlite3
import os
import hashlib
from datetime import date
import collections
# https://docs.python.org/3/library/sqlite3.html
from os import path

ROOT = path.dirname(path.realpath(__file__))

db = path.join(ROOT,"storage.db")

app = Flask(__name__)

file_location = os.path.realpath(os.path.join(
    os.getcwd(), os.path.dirname(__file__)))

acceptedWorkouts = ["squat", "bench", "overhead", "deadlift"]


def hash(data):
    return hashlib.sha224(data.replace('\n', '').encode('ascii')).hexdigest()


# def createTable():
#     adminpass = hash("supersecret")
#     conn = sqlite3.connect(db)
#     c = conn.cursor()
#     c.execute("drop table if exists users")
#     c.execute(
#         "create table if not exists users(username string, password string) ")
#     c.execute(
#         "insert into users (username, password) values ('admin','" + (adminpass) + "')")
#     conn.commit()


# def createUserMax():
#     conn = sqlite3.connect(db)
#     c = conn.cursor()
#     c.execute("drop table if exists usersmax")
#     c.execute("create table if not exists usersmax(username string, squat string, bench string, deadlift string, overhead string)")
#     conn.commit()


# def testUserMax():
#     conn = sqlite3.connect(db)
#     c = conn.cursor()
#     c.execute("INSERT INTO usersmax (username, squat, bench, deadlift, overhead) values ('test', 260, 170, 340, 90)")
#     conn.commit()


def validate(testStr):
    validity = False
    invalid = "!@#$%^&*()+=-[]\\\';,./{}|\":<>?"
    if any(ch in invalid for ch in testStr):
        validity = False
    else:
        validity = True
    return validity


def getUserMax(username):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    result = c.execute("SELECT * FROM usersmax WHERE username=:username",
                       {"username": username}).fetchone()
    maxDict = {}
    try:
        squatMax = result[1]
        benchMax = result[2]
        deadliftMax = result[3]
        overheadMax = result[4]
        maxDict["squat"] = squatMax
        maxDict["bench"] = benchMax
        maxDict["deadlift"] = deadliftMax
        maxDict["overhead"] = overheadMax
        return maxDict
    except:
        maxDict["squatMax"] = '0'
        maxDict["benchMax"] = '0'
        maxDict["deadliftMax"] = '0'
        maxDict["overheadMax"] = '0'
        return maxDict


# def addUserIntoUsermax(username):
#     try:
#         conn = sqlite3.connect(db)
#         c = conn.cursor()
#         c.execute("INSERT INTO usersmax (username, squat, bench, deadlift, overhead) values (:username, '0', '0', '0', '0')", {
#                   "username": username})
#         conn.commit()
#         return True
#     except:
#         return False

def createNewUser(username, hashpass):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("INSERT INTO usersmax (username, squat, bench, deadlift, overhead) values (:username, '0', '0', '0', '0')", {
                  "username": username})
        c.execute("INSERT INTO users (username, password) values (:username, :password)",
                          {"username": username, "password": hashpass})
        conn.commit()
        return True
    except:
        return False

def updateMax(workout, weight, username):
    # def updateMax():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    updateQuery = (
        f"UPDATE usersmax SET '{workout}' = '{weight}' WHERE username = '{username}'")
    # c.execute("UPDATE usersmax SET :workout = :weight WHERE username = :username", {"workout":workout, "weight":weight, "username":username})
    # c.execute("UPDATE usersmax SET squat = ? WHERE username = ?", (weight, username))
    c.execute(updateQuery)
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
            c.execute("SELECT * FROM users WHERE username=:username AND password=:password",
                      {"username": username, "password": hashpass})
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
        if not validate(username) or not validate(password):
            return render_template('register.html', error="username or password contains invalid characters.")

        hashpass = hash(password)
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            result = c.execute("SELECT * FROM users WHERE username=:username",
                      {"username": username}).fetchone()
            conn.commit()
            # rval = c.fetchone()
            if not result:
                status = createNewUser(username, hashpass)
                # c.execute("insert into users (username, password) values (:username, :password)",
                #           {"username": username, "password": hashpass})
                # conn.commit()
                # status = addUserIntoUsermax(username)
                print(status)
            else:
                return render_template("register.html", error="username already exists!")
        except:
            print("error")
            return render_template('register.html', error="error creating a new user, contact admin.")
        return redirect('/home')

@app.route('/home', methods=['GET'])
def main():
    if not 'username' in session:
        return redirect("/login", 303)
    else:
        # updateMax()
        today = date.today()
        todayDate = today.strftime("%B %d, %Y")
        username = session['username'][0]
        maxes = getUserMax(username)
        print(f"username: {session['username'][0]}")
        return render_template('home.html', name=session['username'][0], maxes=maxes, date=todayDate)


# acceptedWorkouts = ["squat", "bench", "overhead", "deadlift"]

def genBoards():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    results = c.execute("SELECT * FROM usersmax").fetchall()
    squatBoard = {}
    benchBoard = {}
    overheadBoard = {}
    deadliftBoard = {}

    boards = [squatBoard, benchBoard, overheadBoard, deadliftBoard]
    boardsSorted = []
    for i in range(0, len(results)): 
        squatBoard[results[i][0]] = results[i][1]
        benchBoard[results[i][0]] = results[i][2]
        overheadBoard[results[i][0]] = results[i][3]
        deadliftBoard[results[i][0]] = results[i][4]
    for board in boards:
        boardsSorted.append(dict(sorted(board.items(), key=lambda x:x[1], reverse=True)))
    return boardsSorted

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    if not 'username' in session:
        return redirect("/login", 303)
    else:
        
        # parse results then send to html
        # username = session['username'][0]
        
        # print(boardsSorted)
        # squatBoardSorted = sorted(squatBoard.items(), key=lambda x:x[1], reverse=True)
        # squatBoardSorted = dict(squatBoardSorted)
        boardsSorted = genBoards()
        return render_template('leaderboard.html', boardsSorted=boardsSorted)


@app.route('/update/<string:workout>', methods=['GET', 'POST'])
def update(workout):
    if not 'username' in session:
        return redirect("/login", 303)
    else:
        if request.method == 'GET':
            workoutName = workout.lower()
            return render_template('updatemax.html', workoutName=workoutName, returnName=workout)
        elif request.method == 'POST':
            # check to make sure that workout is one of four
            if workout in acceptedWorkouts:
                weight = request.form['weight']
                if weight.isdigit():
                    username = session['username'][0]
                    updateMax(workout, weight, username)
                    return redirect('/home')
                else:
                    return render_template('updatemax.html', error="weight was somehow not a digit.")
            else:
                return render_template('updatemax.html', error="workout was somehow not accepted.")
# @app.route('/updatemax', methods=['GET', 'POST'])
# def updatemax():
#     if not 'username' in session:
#         return redirect("/login", 303)
#     else:
#         if request.method == 'GET':
#             return render_template('updatemax.html')
#         if request.method == 'POST':
#             pass


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
    # createTable()
    # createUserMax()
    # testUserMax()
    # app.run(host="localhost", debug=True)
    # app.run(host="10.80.178.102", debug=True)
    # app.run(host="10.80.178.102")
    app.run(host="0.0.0.0")
