from flask import Flask, render_template, redirect, url_for, request, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import crypt
from hmac import compare_digest as compare_hash
from os import environ


mysql_host = environ.get('mysql_host','gnuu.mysql')
mysql_port = environ.get('mysql_port',3306)
mysql_user = environ.get('mysql_user')
mysql_password = environ.get('mysql_password')
mysql_db = environ.get('mysql_db')

app = Flask(__name__)

app.secret_key = 'your-secret-key'

app.config['MYSQL_HOST'] = mysql_host
app.config['MYSQL_PORT'] = mysql_port
app.config['MYSQL_USER'] = mysql_user
app.config['MYSQL_PASSWORD'] = mysql_password
app.config['MYSQL_DB'] = mysql_db

# Intialize MySQL
mysql = MySQL(app)

@app.route('/cgi-bin/user.cgi', methods=['GET', 'POST'])
def user():
    msg = ''
    if session['loggedin'] == True:
        if request.method == 'POST' and 'site' in request.form:
            site = request.form['site']
            anrede = request.form['anrede']
            vorname = request.form['vorname']
            nachname = request.form['nachname']
            strasse1 = request.form['strasse1']
            strasse2 = request.form['strasse2']
            land = request.form['land']
            plz = request.form['plz']
            ort = request.form['ort']
            telefon = request.form['telefon']
            telefax = request.form['telefax']
            email = request.form['email']
            geburtstag = request.form['geburtstag']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('"UPDATE user SET anrede = %s , vorname = %s, nachname = %s, strasse1 = %s, strasse2 = %s, land = %s, plz = %s, ort = %s, telefon = %s, telefax = %s, email = %s, geburtstag = %s WHERE site = %s ', (anrede,vorname,nachnahme,strasse1,strasse2,land,plz,orrt,telefon,telefax,email,geburtstag,site))
            return render_template('user.html', msg=msg)
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM user WHERE site = %s ', (site))
            account = cursor.fetchone()
            if account:
                anrede = account['anrede']
                vorname = account['vorname']
                nachname = account['nachname']
                strasse1 = account['strasse1']
                strasse2 = account['strasse2']
                land = account['land']
                plz = account['plz']
                ort = account['ort']
                telefon = account['telefon']
                telefax = account['telefax']
                email = account['email']
                geburtstag = account['geburtstag']
        return render_template('user.html', msg=msg)
    else:
        return redirect(url_for('login'))

@app.route('/cgi-bin/login.cgi', methods=['GET', 'POST'])
def login():
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE site = %s ', (username))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['site']
            cryptedpasswd = account['password']

            ## compare_hash(crypt.crypt(cleartext, cryptedpasswd), cryptedpasswd)
            if compare_hash(crypt.crypt(password, cryptedpasswd), cryptedpasswd):
            # Redirect to home page
                return redirect(url_for('user'))
                #return 'Logged in successfully!'
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

@app.route('/cgi-bin/logout.cgi')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('site', None)
   # Redirect to login page
   return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

if __name__ == '__main__':

  app.run(
    host = "0.0.0.0",
    port = 5000
  )

