#!/usr/bin/env python3

# https://docs.python.org/3/library/sqlite3.html

from flask import jsonify
from flask import Flask, render_template, request, redirect, session, send_from_directory, make_response
import sqlite3
import hashlib
from datetime import date
from os import path
import math
# from testsuite import *

ROOT = path.dirname(path.realpath(__file__))

db = path.join(ROOT, "storage.db")
app = Flask(__name__)
with open(path.join(ROOT, "secrets.txt"), 'r') as f:
    s = f.readlines()
app.secret_key = s[0].replace('\n', '')
app.config.update(SESSION_COOKIE_HTTPONLY=False)

acceptedWorkouts = ["squat", "bench", "overhead", "deadlift"]


def hash(data):
    return hashlib.sha224(data.replace('\n', '').encode('ascii')).hexdigest()


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

def sortBoard(board):
    return dict(sorted(board.items(), key=lambda x: x[1], reverse=True))

def genBoards():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    results = c.execute("SELECT * FROM usersmax").fetchall()
    squatRes = {}
    benchRes = {}
    deadliftRes = {}
    overheadRes = {}

    squatBoard = {}
    benchBoard = {}
    overheadBoard = {}
    deadliftBoard = {}
    boards = [squatBoard, benchBoard, deadliftBoard, overheadBoard]
    for i in range(0, len(results)):
        squatRes[results[i][0]] = results[i][1]
        benchRes[results[i][0]] = results[i][2]
        deadliftRes[results[i][0]] = results[i][3]
        overheadRes[results[i][0]] = results[i][4]
    squatBoard["squat"] = sortBoard(squatRes)
    benchBoard["bench"] = sortBoard(benchRes)
    deadliftBoard["deadlift"] = sortBoard(deadliftRes)
    overheadBoard["overhead"] = sortBoard(overheadRes)
    return boards


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
            conn = sqlite3.connect(db)
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
            if not result:
                status = createNewUser(username, hashpass)
                print(status)
            else:
                return render_template("register.html", error="username already exists!")
        except:
            print("error")
            return render_template('register.html', error="error creating a new user, contact admin.")
        return redirect('/home')


@app.route('/home', methods=['GET'])
def home():
    if not 'username' in session:
        return redirect("/login", 303)
    else:
        today = date.today()
        todayDate = today.strftime("%B %d, %Y")
        username = session['username'][0]
        maxes = getUserMax(username)
        print(f"username: {session['username'][0]}")
        return render_template('home.html', name=session['username'][0], maxes=maxes, date=todayDate)


@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    if not 'username' in session:
        return redirect("/login", 303)
    else:
        boardsSorted = genBoards()
        return render_template('leaderboard.html', boardsSorted=boardsSorted)


@app.route('/public/leaderboard', methods=["GET"])
def publicLeaderboard():
    boardsSorted = genBoards()
    return jsonify(leaderboard=boardsSorted)
    # return temp


@app.route('/update/<string:workout>', methods=['GET', 'POST'])
def update(workout):
    if not 'username' in session:
        return redirect("/login", 303)
    else:
        if request.method == 'GET':
            workoutName = workout.lower()
            return render_template('updatemax.html', workoutName=workoutName, returnName=workout)
        elif request.method == 'POST':
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


def calcPlates(weight):
    results = {}
    perSide = (weight-45)/2
    num45 = math.floor(perSide / 45)
    num25 = math.floor((perSide - (num45*45))/25)
    num10 = math.floor((perSide - (num45*45) - (num25*25))/10)
    num5 = math.floor((perSide - (num45*45) - (num25*25) - (num10*10))/5)
    num2_5 = math.floor(
        (perSide - (num45*45) - (num25*25) - (num10*10) - (num5*5))/2.5)
    results['45'] = num45
    results['25'] = num25
    results['10'] = num10
    results['5'] = num5
    results['2.5'] = num2_5
    totalWeight = (num45*45 + num25*25 + num10*10 + num5*5 + num2_5*2.5)*2 + 45
    return (results, totalWeight)


@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if not 'username' in session:
        return redirect("/login", 303)
    else:
        if request.method == 'GET':
            return render_template('calculator.html')
        elif request.method == 'POST':
            results = {}
            totalWeight = float(request.form.get("weight"))
            if totalWeight < 45.0:
                return render_template('calculator.html', error="Do the math yourself")
            else:
                results = calcPlates(totalWeight)
                return render_template('calculator.html', data=results[0], weight=results[1])


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect("/", 303)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
