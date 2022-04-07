
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


def createUserMax():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("drop table if exists usersmax")
    c.execute("create table if not exists usersmax(username string, squat string, bench string, deadlift string, overhead string)")
    conn.commit()


def testUserMax():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("INSERT INTO usersmax (username, squat, bench, deadlift, overhead) values ('test', 260, 170, 340, 90)")
    conn.commit()


def addUserIntoUsermax(username):
    try:
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("INSERT INTO usersmax (username, squat, bench, deadlift, overhead) values (:username, '0', '0', '0', '0')", {
                  "username": username})
        conn.commit()
        return True
    except:
        return False


@app.route('/updatemax', methods=['GET', 'POST'])
def updatemax():
    if not 'username' in session:
        return redirect("/login", 303)
    else:
        if request.method == 'GET':
            return render_template('updatemax.html')
        if request.method == 'POST':
            pass