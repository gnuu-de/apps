from flask import Flask, render_template, redirect, url_for, request, session, make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import crypt
from hmac import compare_digest as compare_hash
from os import environ
import secrets
import random
import string
import requests
from marshmallow import Schema, fields
from marshmallow.validate import Length, Range
from flask_mail import Mail, Message

mysql_host = environ.get('mysql_host','localhost')
mysql_port = environ.get('mysql_port',3306)
mysql_user = environ.get('mysql_user')
mysql_password = environ.get('mysql_password')
mysql_db = environ.get('mysql_db')

twilio_gateway_uri = environ.get('twilio_gateway_uri')
twilio_identifier = environ.get('twilio_identifier')
twilio_from = environ.get('twilio_from')
twilio_to = environ.get('twilio_to')

app = Flask(__name__)

app.secret_key = 'your-secret-key'

app.config['MYSQL_HOST'] = mysql_host
app.config['MYSQL_PORT'] = mysql_port
app.config['MYSQL_USER'] = mysql_user
app.config['MYSQL_PASSWORD'] = mysql_password
app.config['MYSQL_DB'] = mysql_db

app.config['TWILIO_GATEWAY_URI'] = twilio_gateway_uri
app.config['TWILIO_IDENTIFIER'] = twilio_identifier
app.config['TWILIO_FROM'] = twilio_from
app.config['TWILIO_TO'] = twilio_to

app.config['MAIL_SERVER']='mail'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)
mysql = MySQL(app)

class ValidateInputSchemaSMS(Schema):
    body = fields.Str(required=True, validate=Length(min=1,max=64))
    checkfield = fields.Str(required=True, validate=Length(max=6))
    hcheck = fields.Str(required=True, validate=Length(max=6))

class ValidateInputSchemaEmail(Schema):
    email = fields.Email(required=False, validate=Length(max=64))
    subject = fields.Str(required=True, validate=Length(min=1,max=255))
    body = fields.Str(required=True, validate=Length(min=1,max=2000))
    checkfield = fields.Str(required=True, validate=Length(max=6))
    hcheck = fields.Str(required=True, validate=Length(max=6))

class ValidateInputSchemaPwfailed(Schema):
    site = fields.Str(required=True, validate=Length(min=13,max=13))
    password = fields.Str(required=False, validate=Length(min=8,max=64))
    pwquestion = fields.Str(required=True, validate=Length(min=1,max=64))
    pwanswer = fields.Str(required=True, validate=Length(min=1,max=64))

class ValidateInputSchemaAdduser(Schema):
    site = fields.Str(required=True, validate=Length(max=13))
    password = fields.Str(required=True, validate=Length(min=8,max=64))
    email = fields.Email(required=True, validate=Length(min=4,max=128))
    pwquestion = fields.Str(required=True, validate=Length(min=1,max=255))
    pwanswer = fields.Str(required=True, validate=Length(min=1,max=255))
    checkfield = fields.Str(required=True, validate=Length(min=6,max=6))
    hcheck = fields.Str(required=True, validate=Length(min=6,max=6))

class ValidateInputSchemaConf(Schema):
    site = fields.Str(required=True, validate=Length(min=13,max=13))
    newsgroups = fields.Str(required=True)
    pathexcludes = fields.Str(required=False, validate=Length(max=64))
    maxcross = fields.Int(required=True, validate=Range(min=0,max=99))
    maxsize = fields.Int(required=True, validate=Range(min=5000,max=1000000))
    ownarticles = fields.Str(required=False)
    compression = fields.Str(required=True, validate=Length(min=3,max=64))
    maxbatchsize = fields.Int(required=True, validate=Range(min=0,max=1000000))
    batchtime = fields.Int(required=True, validate=Range(min=300,max=86400))
    subdomain1 = fields.Str(required=False)
    subdomain2 = fields.Str(required=False)
    subdomain3 = fields.Str(required=False)
    subdomain4 = fields.Str(required=False)
    subdomain5 = fields.Str(required=False)
    subdomain6 = fields.Str(required=False)
    subdomain7 = fields.Str(required=False)
    subdomain8 = fields.Str(required=False)
    subdomain9 = fields.Str(required=False)
    subdomain10 = fields.Str(required=False)

class ValidateInputSchemaUser(Schema):
    site = fields.Str(required=True, validate=Length(min=13,max=13))
    anrede = fields.Str(required=True, validate=Length(max=10))
    vorname = fields.Str(required=True, validate=Length(max=64))
    nachname = fields.Str(required=True, validate=Length(max=64))
    strasse1 = fields.Str(required=True, validate=Length(max=128))
    strasse2 = fields.Str(required=False, validate=Length(max=128))
    land = fields.Str(required=True, validate=Length(max=2))
    plz = fields.Int(required=True)
    ort = fields.Str(required=False, validate=Length(max=128))
    telefon = fields.Str(required=False, validate=Length(max=64))
    telefax = fields.Str(required=False, validate=Length(max=64))
    email = fields.Email(required=True, validate=Length(max=128))
    geburtstag = fields.Str(required=False, validate=Length(max=10))

class ValidateInputSchemaLogin(Schema):
    username = fields.Str(required=True, validate=Length(max=13))
    password = fields.Str(required=False, validate=Length(max=64))

validate_input_schema_sms = ValidateInputSchemaSMS()
validate_input_schema_email = ValidateInputSchemaEmail()
validate_input_schema_pw_failed = ValidateInputSchemaPwfailed()
validate_input_schema_adduser = ValidateInputSchemaAdduser()
validate_input_schema_conf = ValidateInputSchemaConf()
validate_input_schema_user = ValidateInputSchemaUser()
validate_input_schema_login = ValidateInputSchemaLogin()


@app.route('/cgi-bin/notfall.cgi', methods=['GET', 'POST'])
def notfall():
    msg = ''
    letters = string.ascii_lowercase
    checkfield = ''.join(random.sample(letters, 5))
    if request.method == 'POST' and 'body' in request.form:
        checkfield = request.form['checkfield']
        hcheck = request.form['hcheck']
        body = request.form['body']
        errors = validate_input_schema_sms.validate(request.form)
        if errors:
            return render_template('notfall.html',msg=str(errors),body=body,checkfield=checkfield)
        if checkfield == hcheck:
            data = {
              "From": twilio_from,
              "To": twilio_to,
              "Body": body
            }
            uri = "https://" + twilio_identifier + "@" + twilio_gateway_uri
            twilio = requests.post(uri, data=data)
            msg = 'Gateway status: %s' % twilio.ok
            return render_template('notfall.html',msg=msg)
        else:
            msg = "checkfield was wrong"
            return render_template('notfall.html',msg=msg,body=body,checkfield=checkfield)
    else:
        return render_template('notfall.html',checkfield=checkfield)

    return render_template('notfall.html',checkfield=checkfield)

@app.route('/cgi-bin/email.cgi', methods=['GET', 'POST'])
def email():
    msg = ''
    letters = string.ascii_lowercase
    checkfield = ''.join(random.sample(letters, 5))
    if request.method == 'POST' and 'email' in request.form:
        checkfield = request.form['checkfield']
        hcheck = request.form['hcheck']
        email = request.form['email']
        subject = request.form['subject']
        body = request.form['body']
        errors = validate_input_schema_email.validate(request.form)
        if errors:
            return render_template('mail.html',msg=str(errors),email=email,subject=subject,body=body,checkfield=checkfield)
        if checkfield == hcheck:
            webmsg = Message(subject, sender = 'eumel@admin.gnuu.de', recipients = ['eumel@admin.gnuu.de'])
            webmsg.body = "%s\n\n%s" % (email,body)
            mail.send(webmsg)

            msg = 'Nachricht gesendet'
            return render_template('mail.html',msg=msg)
        else:
            msg = "checkfield was wrong"
            return render_template('mail.html',msg=msg,email=email,subject=subject,body=body,checkfield=checkfield)
    else:
        return render_template('mail.html',checkfield=checkfield)

    return render_template('mail.html',checkfield=checkfield)


@app.route('/cgi-bin/adduser.cgi', methods=['GET', 'POST'])
def adduser():
    msg = ''
    letters = string.ascii_lowercase
    checkfield = ''.join(random.sample(letters, 5))
    if request.method == 'POST' and 'site' in request.form:
        checkfield = request.form['checkfield']
        hcheck = request.form['hcheck']
        site = request.form['site']
        email = request.form['email']
        password = request.form['password']
        cryptpassword = crypt.crypt(password,crypt.METHOD_CRYPT)
        pwquestion = request.form['pwquestion']
        pwanswer = request.form['pwanswer']
        cryptpwanswer = crypt.crypt(pwanswer,crypt.METHOD_CRYPT)
        status = 0
        errors = validate_input_schema_adduser.validate(request.form)
        if errors:
            return render_template('adduser.html',msg=str(errors),site=site,email=email,password=password,pwquestion=pwquestion,pwanswer=pwanswer,checkfield=checkfield)
        if checkfield == hcheck:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('''INSERT into user (site,status,password,email,pwquestion,pwanswer) VALUES (%s,%s,%s,%s,%s,%s)''', (site,status,cryptpassword,email,pwquestion,cryptpwanswer))
            msg = 'Account hinzugefuegt'
            return render_template('index.html',msg=msg)
            #return render_template('adduser.html',msg=msg)
        else:
            msg = "checkfield was wrong"
            return render_template('adduser.html',msg=msg,site=site,email=email,password=password,pwquestion=pwquestion,pwanswer=pwanswer,checkfield=checkfield)
    else:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''SELECT site FROM user ORDER by site desc limit 1''')
        account = cursor.fetchone()
        if account:
            site = int(account['site']) + 1
            return render_template('adduser.html',msg=msg,site=site,checkfield=checkfield)
    return render_template('adduser.html',checkfield=checkfield)

@app.route('/cgi-bin/pw_failed.cgi', methods=['GET', 'POST'])
def pw_failed():
    msg = ''
    if request.method == 'POST' and 'site' in request.form:
        errors = validate_input_schema_pw_failed.validate(request.form)
        if errors:
            return render_template('pw_failed.html',msg=str(errors))
        site = request.form['site']
        password = request.form['password']
        cryptedpassword = crypt.crypt(password,crypt.METHOD_CRYPT)
        pwquestion = request.form['pwquestion']
        pwanswer = request.form['pwanswer']
        cryptedpwanswer = crypt.crypt(pwanswer,crypt.METHOD_CRYPT)
        status = 0
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE site = %s ', (site,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            clearpwquestion  = account['pwquestion']
            cryptedpwanswer = account['pwanswer']

            if compare_hash(crypt.crypt(pwanswer, cryptedpwanswer), cryptedpwanswer):
                msg = 'Passwortantwort war richtig'
                if clearpwquestion == pwquestion:
                    msg = msg + ' + Passwortfrage war richtig'
                    cursor.execute('UPDATE user SET failed = 0 WHERE site = %s',(site,))
                    if password:
                        cursor.execute('UPDATE user set password = %s WHERE site = %s',(cryptedpassword,site,))
                        msg = msg + " + Passwort geaendert"
                    else:
                        cursor.execute('UPDATE user set pwquestion = %s, pwanswer = %s WHERE site = %s',(pwquestion, cryptedpwanswer,site,))
                        msg = msg + " + Passwortfrage/antwort geaendert"
                return render_template('pw_failed.html',msg=msg,site=site)
            else:
                msg = 'Passwortantwort war falsch'
                return render_template('pw_failed.html',msg=msg,site=site)

        msg = 'No account found!'
        return render_template('pw_failed.html',msg=msg,site=site)
    else:
        return render_template('pw_failed.html')


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
    msg = 'Keine Rechnungsdaten'
    return render_template('billing.html', msg=msg)



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
            errors = validate_input_schema_conf.validate(request.form)
            if errors:
                return render_template('conf.html',msg=str(errors),site=site,newsgroups=newsgroups,pathexcludes=pathexcludes,maxcross=maxcross,maxsize=maxsize,ownarticles=ownarticles,compression=compression,maxbatchsize=maxbatchsize,batchtime=batchtime,dc=dc)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE conf SET newsgroups = %s , pathexcludes = %s, maxcross = %s, maxsize = %s, ownarticles = %s, compression = %s, maxbatchsize = %s, batchtime = %s WHERE site = %s ', (newsgroups,pathexcludes,maxcross,maxsize,ownarticles,compression,maxbatchsize,batchtime,site))

            cursor.execute('UPDATE transport SET status = 1 WHERE dst = %s ', ("bsmtp:"+site,))
            for dcc in request.form.getlist('subdomain1'):
                userdomain = dcc.split(";",1)
                cursor.execute('UPDATE transport SET status = 0 WHERE src = %s ', (userdomain[1],))
            cursor.execute('SELECT src,status FROM transport WHERE dst=%s', ("bsmtp:"+site,))
            mailtransportdata = cursor.fetchall()
            jobapi = requests.get("http://job/update/configmaps")
            msg = 'Daten aktualisiert: %s' % jobapi.text
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
            errors = validate_input_schema_user.validate(request.form)
            if errors:
                return render_template('user.html',msg=str(errors),site=site,anrede=anrede,vorname=vorname,nachname=nachname,strasse1=strasse1,strasse2=strasse2,land=land,plz=plz,ort=ort,telefon=telefon,telefax=telefax,email=email,geburtstag=geburtstag,billingsum=billingsum)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE user SET anrede = %s , vorname = %s, nachname = %s, strasse1 = %s, strasse2 = %s, land = %s, plz = %s, ort = %s, telefon = %s, telefax = %s, email = %s, geburtstag = %s WHERE site = %s ', (anrede,vorname,nachname,strasse1,strasse2,land,plz,ort,telefon,telefax,email,geburtstag,site))
            msg = 'Account aktualisiert'
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
    return redirect(url_for('login'))

@app.route('/cgi-bin/login.cgi', methods=['GET', 'POST'])
def login():
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        errors = validate_input_schema_login.validate(request.form)
        if errors:
            return render_template('index.html',msg=str(errors))
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE failed < 6 AND site = %s ', (username,))
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
                cursor.execute('UPDATE user SET failed = 0 WHERE site = %s',(username,))
                cursor.execute('REPLACE INTO sessions (id, site) VALUES (%s,%s)',(cookie, username,))
                response = make_response(redirect(url_for('user')))
                response.set_cookie("gnuu",cookie)
                return response
            else:
                cursor.execute('UPDATE user set failed = failed + 1 WHERE site = %s',(username,))
                msg = 'Passwort ist falsch!'
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Falscher Username/Passwort!'
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

@app.route('/cgi-bin/logout.cgi')
def logout():
    # Remove session data, this will log the user out
    cookie = request.cookies.get('gnuu')
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('site', None)
    if cookie:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM sessions WHERE id = %s',(cookie,))
        response = make_response(redirect(url_for('login')))
        response.set_cookie("gnuu",cookie, max_age=0)
        return response
    else:
        return render_template('index.html', msg=msg)

@app.route('/cgi-bin/index.html')
def index():
    return redirect('/')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':

  app.run(
    host = "0.0.0.0",
    port = 5000,
    debug = 0
  )
