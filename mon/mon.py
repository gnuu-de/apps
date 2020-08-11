from flask import Flask, request
from flask_mysqldb import MySQL
import MySQLdb.cursors
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

mysql = MySQL(app)

@app.route('/metrics', methods=['GET', 'POST'])
def metrics():
    counter = ""

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('select count(*) as repomirror from repomirrorconfig where is_enabled = 1')
    result = cursor.fetchone()
    if result:
        counter = "python_quay_repomirror_count " + str(result['repomirror']) + "\n"
    cursor.execute('select count(*) as image from image')
    result = cursor.fetchone()
    if result:
        counter += "python_quay_image_count " + str(result['image']) + "\n"
    cursor.execute('select count(*) as repository from repository')
    result = cursor.fetchone()
    if result:
        counter += "python_quay_repository_count " + str(result['repository']) + "\n"
    cursor.execute('select sum(image_size)/1024/1024/1024 as storage_size_gb from imagestorage;')
    result = cursor.fetchone()
    if result:
        counter += "python_quay_storage_size_gb " + str(result['storage_size_gb']) + "\n"
    return counter, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':

  app.run(
    host = "0.0.0.0",
    port = 9091,
    debug = 0
  )
