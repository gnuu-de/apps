from flask import Flask, redirect, url_for, request
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from hmac import compare_digest as compare_hash
from os import environ


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

@app.route('/update/news', methods=['GET', 'POST'])
def news():
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    #cursor.execute('SELECT * FROM sessions WHERE id = %s', (cookie,))
    cursor.execute('SELECT * FROM sessions')
    cookiesession = cursor.fetchone()
    if cookiesession:
        site = cookiesession['site']
        cursor.execute('SELECT site,vorname,nachname,email FROM user ORDER BY site')
        groupdata = cursor.fetchall()
        if groupdata:
            return redirect("/")

@app.route('/update/uucp', methods=['GET', 'POST'])
def uucp():
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT site,password,failed  FROM user WHERE pwquestion != ""')
    passwords = cursor.fetchall()
    if passwords:
        for passwd in passwords:
            site = passwd['site']
            pword = passwd['password']
            failed = passwd['failed']
            if failed < 6:
                with open("passwd","wb") as fi:
                    fi.write(site + " " + password)
    return redirect("/")

if __name__ == '__main__':

  app.run(
    host = "0.0.0.0",
    port = 5000,
    debug = 1
  )
