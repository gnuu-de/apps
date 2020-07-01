from flask import Flask, render_template, redirect, url_for, request, session, make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import crypt
from hmac import compare_digest as compare_hash
from os import environ
import secrets


mysql_host = environ.get('mysql_host','localhost')
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

@app.route('/cgi-bin/group.cgi', methods=['GET', 'POST'])
def group():
    msg = ''
    cookie = request.cookies.get('gnuu')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM sessions WHERE id = %s', (cookie,))
    cookiesession = cursor.fetchone()
    if cookiesession:
        site = cookiesession['site']
        cursor.execute('SELECT site,vorname,nachname,email FROM user ORDER BY site')
        groupdata = cursor.fetchall()
        if groupdata:
            return render_template('group.html', site=site, groupdata=groupdata)

@app.route('/cgi-bin/billing.cgi', methods=['GET', 'POST'])
def billing():
    msg = ''
    cookie = request.cookies.get('gnuu')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM sessions WHERE id = %s', (cookie,))
    cookiesession = cursor.fetchone()
    if cookiesession:
        site = cookiesession['site']
        cursor.execute('SELECT * FROM billing WHERE site = %s ORDER BY id', (site,))
        billingdata = cursor.fetchall()
        if billingdata:
            return render_template('billing.html', site=site, billingdata=billingdata)


@app.route('/cgi-bin/conf.cgi', methods=['GET', 'POST'])
def conf():
    msg = ''
    ownarticles = 0
    dc = 1
    cookie = request.cookies.get('gnuu')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM sessions WHERE id = %s', (cookie,))
    cookiesession = cursor.fetchone()
    if cookiesession:
        site = cookiesession['site']
        if request.method == 'POST' and 'site' in request.form:
            site = request.form['site']
            newsgroups = request.form['newsgroups']
            pathexcludes = request.form['pathexcludes']
            maxcross = request.form['maxcross']
            maxsize = request.form['maxsize']
            ownanswer = request.form.getlist('ownarticles')
            if ownanswer:
                ownarticles = 1
            compression = request.form['compression']
            maxbatchsize = request.form['maxbatchsize']
            batchtime = request.form['batchtime']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE conf SET newsgroups = %s , pathexcludes = %s, maxcross = %s, maxsize = %s, ownarticles = %s, compression = %s, maxbatchsize = %s, batchtime = %s WHERE site = %s ', (newsgroups,pathexcludes,maxcross,maxsize,ownarticles,compression,maxbatchsize,batchtime,site))

            cursor.execute('UPDATE transport SET status = 1 WHERE dst = %s ', ("bsmtp:"+site,))
            for dcc in request.form.getlist('subdomain1'):
                userdomain = dcc.split(";",1)
                cursor.execute('UPDATE transport SET status = 0 WHERE src = %s ', (userdomain[1],))
            cursor.execute('SELECT src,status FROM transport WHERE dst=%s', ("bsmtp:"+site,))
            mailtransportdata = cursor.fetchall()
            if mailtransportdata:
                return render_template('conf.html', msg=msg,site=site,newsgroups=newsgroups,pathexcludes=pathexcludes,maxcross=maxcross,maxsize=maxsize,ownarticles=ownarticles,compression=compression,maxbatchsize=maxbatchsize,batchtime=batchtime,dc=dc,mailtransportdata=mailtransportdata)
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM conf WHERE site = %s ', (site,))
            account = cursor.fetchone()
            if account:
                newsgroups = account['newsgroups']
                pathexcludes = account['pathexcludes']
                maxcross = account['maxcross']
                maxsize = account['maxsize']
                if (account['ownarticles'] == 1):
                    ownarticles = 'checked' 
                compression = account['compression']
                maxbatchsize = account['maxbatchsize']
                batchtime = account['batchtime']
            cursor.execute('SELECT src,status FROM transport WHERE dst=%s', ("bsmtp:"+site,))
            mailtransportdata = cursor.fetchall()
            if mailtransportdata:
                return render_template('conf.html', msg=msg,site=site,newsgroups=newsgroups,pathexcludes=pathexcludes,maxcross=maxcross,maxsize=maxsize,ownarticles=ownarticles,compression=compression,maxbatchsize=maxbatchsize,batchtime=batchtime,dc=dc,mailtransportdata=mailtransportdata)
    else:
        return redirect(url_for('login'))

@app.route('/cgi-bin/user.cgi', methods=['GET', 'POST'])
def user():
    msg = ''
    billingsum = "0"
    cookie = request.cookies.get('gnuu')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM sessions WHERE id = %s', (cookie,))
    cookiesession = cursor.fetchone()
    if cookiesession:
        site = cookiesession['site']
        cursor.execute('SELECT SUM(euro) as sum FROM billing WHERE site = %s', (site,))
        billing = cursor.fetchone()
        if billing:
            billingsum = str(billing['sum']) + " EURO"
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
            cursor.execute('UPDATE user SET anrede = %s , vorname = %s, nachname = %s, strasse1 = %s, strasse2 = %s, land = %s, plz = %s, ort = %s, telefon = %s, telefax = %s, email = %s, geburtstag = %s WHERE site = %s ', (anrede,vorname,nachname,strasse1,strasse2,land,plz,ort,telefon,telefax,email,geburtstag,site))
            return render_template('user.html', msg=msg,site=site,anrede=anrede,vorname=vorname,nachname=nachname,strasse1=strasse1,strasse2=strasse2,land=land,plz=plz,ort=ort,telefon=telefon,telefax=telefax,email=email,geburtstag=geburtstag,billingsum=billingsum)
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM user WHERE site = %s ', (site,))
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
        return render_template('user.html', msg=msg,site=site,anrede=anrede,vorname=vorname,nachname=nachname,strasse1=strasse1,strasse2=strasse2,land=land,plz=plz,ort=ort,telefon=telefon,telefax=telefax,email=email,geburtstag=geburtstag,billingsum=billingsum)
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
        cursor.execute('SELECT * FROM user WHERE site = %s ', (username,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['site']
            cryptedpasswd = account['password']

            if compare_hash(crypt.crypt(password, cryptedpasswd), cryptedpasswd):
                session['gnuu'] = secrets.token_urlsafe(20)
                cookie = session['gnuu']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('REPLACE INTO sessions (id, site) VALUES (%s,%s)',(cookie, username,))
                response = make_response(redirect(url_for('user')))
                response.set_cookie("gnuu",cookie)
                return response
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

@app.route('/cgi-bin/logout.cgi')
def logout():
    # Remove session data, this will log the user out
   cookie = request.cookies.get('gnuu')
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('site', None)
   cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
   cursor.execute('DELETE FROM sessions WHERE id = %s',(cookie,))
   response = make_response(redirect(url_for('login')))
   response.set_cookie("gnuu",cookie, max_age=0)
   return response

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
    port = 5000,
    debug = 0
  )
