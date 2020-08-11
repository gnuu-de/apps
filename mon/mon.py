from flask import Flask, redirect, url_for, request, jsonify
from flask_prometheus import monitor
from flask_mysqldb import MySQL
import MySQLdb.cursors
import urllib.request
from os import environ
import prometheus_client as prom
import random
import time
from threading import Thread

req_summary = prom.Summary('python_my_req_example', 'Time spent processing a request')

@req_summary.time()
def process_request(t):
    time.sleep(t)

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

mysql = MySQL(app)

@app.route('/metrics', methods=['GET', 'POST'])
def metrics():

    counter = prom.Counter('python_my_counter', 'This is my counter')
    #gauge = prom.Gauge('python_my_gauge', 'This is my gauge')
    #histogram = prom.Histogram('python_my_histogram', 'This is my histogram')
    #summary = prom.Summary('python_my_summary', 'This is my summary')

    #while True:
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('select count(*) as repomirror from repomirrorconfig where is_enabled = 1')
    result = cursor.fetchone()
    if result:
        counter.inc = str(result['repomirror'])
        #counter.inc(random.random())
        #gauge.set(random.random() * 15 - 5)
        #histogram.observe(random.random() * 10)
        #summary.observe(random.random() * 10)
        #process_request(random.random() * 5)
        res.append(prom.generate_latest(counter.inc))
        return Response(res, mimetype="text/plain")

    #    time.sleep(60)

    return "Bad Request", 400, None
#Thread(target=thr).start()

#monitor(app, port=9091)

if __name__ == '__main__':

  app.run(
    host = "0.0.0.0",
    port = 9091,
    debug = 1
  )
