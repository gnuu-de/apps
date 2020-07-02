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

@app.route('/update/uucp/passwd', methods=['GET', 'POST'])
def uucppasswd():
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT site,password FROM user WHERE pwquestion != "" AND failed < 6')
    passwords = cursor.fetchall()
    if passwords:
        fp = open('passwd','w')
        for row in passwords:
            fp.write("%s %s\n" % (str(row["site"]),str(row['password'])))
        fp.close()
    resp = jsonify(success=True)
    return resp

@app.route('/update/uucp/sys', methods=['GET', 'POST'])
def uucpsys():
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT conf.site as site,conf.compression as compression FROM conf,user WHERE conf.site=user.site')
    syss = cursor.fetchall()
    if syss:
        fp = open('sys','w')
        fp.write("# gnuu sys uucp conf\n")
        fp.write("call-login\n")
        fp.write("call-password\n")
        fp.write("time any\n")
        fp.write("port tcp\n")
        fp.write("#\n")
        for row in syss:
            fp.write("system %s\n" % (str(row["site"])))
            fp.write("called-login %s\n" % (str(row["site"])))
            fp.write("remote-receive /data/spool/uucp/%s\n" % (str(row["site"])))
            fp.write("remote-send /data/spool/uucp/%s\n" % (str(row["site"])))
            if row["compression"] == "gzip":
                fp.write("called-chat-program /usr/sbin/batcher g-rcsmtp %s\n" % (str(row["site"])))
            elif row["compression"] == "bzip2":
                fp.write("called-chat-program /usr/sbin/batcher b-rcsmtp %s\n" % (str(row["site"])))
            elif row["compression"] == "szip":
                fp.write("called-chat-program /usr/sbin/batcher s-rcsmtp %s\n" % (str(row["site"])))
            else:
                fp.write("called-chat-program /usr/sbin/batcher c-rcsmtp %s\n" % (str(row["site"])))
            fp.write("commands srnews rmail rsmtp rbsmtp rcsmtp rgsmtp rssmtp\n")
            fp.write("command-path /usr/lib/news/bin /usr/local/bin /usr/bin /usr/local/lib/uucp/\n")
        fp.close()
    resp = jsonify(success=True)
    return resp

@app.route('/update/news/feeds', methods=['GET', 'POST'])
def newsfeeds():
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT site, newsgroups, pathexcludes, maxsize, maxcross, ownarticles FROM conf')
    newsfeeds = cursor.fetchall()
    if newsfeeds:
        fp = open('newsfeeds','wb')
        remotenewsfeeds = urllib.request.urlopen('https://raw.githubusercontent.com/gnuu-de/serverconfig/master/etc/news/newsfeeds.default')
        defaultnewsfeed = remotenewsfeeds.read()
        if defaultnewsfeed:
            fp.write(defaultnewsfeed)
        fp.close()
        fp = open('newsfeeds','a+')
        fp.write("# user newsfeeds\n")
        for row in newsfeeds:
            site = row['site']
            newsgroups = row['newsgroups'].replace(" ", "")
            pathexcludes = row['pathexcludes'].replace(" ", "")
            maxsize = row['maxsize']
            maxcross = row['maxcross']
            ownarticles = row['ownarticles']
            if ownarticles == 1:
                ownarticles = ",Ap"
            fp.write("#\n")
            if pathexcludes:
                fp.write("%s/%s\n" % (str(site),str(pathexcludes)))
            else:
                fp.write("%s/\n" % (str(site)))
            fp.write(":%s\n" % (str(newsgroups)))
            fp.write(":Tf,Wnb,B4096/1024,G%s,<%s%s:%s\n" % (str(maxcross),str(maxsize),str(ownarticles),str(site)))
            fp.write("#\n")
        fp.close()
    resp = jsonify(success=True)
    return resp

@app.route('/update/news/uucp', methods=['GET', 'POST'])
def newsuucp():
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT site, compression, maxbatchsize, batchtime FROM conf')
    batchtimes = cursor.fetchall()
    if batchtimes:
        fp300 = open('send-uucp.cf.300','w')
        fp1800 = open('send-uucp.cf.1800','w')
        fp3600 = open('send-uucp.cf.3600','w')
        fp21600 = open('send-uucp.cf.21600','w')
        fp43200 = open('send-uucp.cf.43200','w')
        fp86400 = open('send-uucp.cf.86400','w')
        for row in batchtimes:
            site = row['site']
            compression = row['compression']
            maxbatchsize = row['maxbatchsize']
            batchtime = row['batchtime']
            if batchtime == 300:
                fp300.write("%s %s %s\n" % (str(site),str(compression),str(maxbatchsize)))
            elif batchtime == 1800:
                fp1800.write("%s %s %s\n" % (str(site),str(compression),str(maxbatchsize)))
            elif batchtime == 3600:
                fp3600.write("%s %s %s\n" % (str(site),str(compression),str(maxbatchsize)))
            elif batchtime == 21600:
                fp21600.write("%s %s %s\n" % (str(site),str(compression),str(maxbatchsize)))
            elif batchtime == 43200:
                fp43200.write("%s %s %s\n" % (str(site),str(compression),str(maxbatchsize)))
            elif batchtime == 86400:
                fp86400.write("%s %s %s\n" % (str(site),str(compression),str(maxbatchsize)))
            else:
                fp3600.write("%s %s %s\n" % (str(site),str(compression),str(maxbatchsize)))
        fp300.close()
        fp1800.close()
        fp3600.close()
        fp21600.close()
        fp43200.close()
        fp86400.close()
    resp = jsonify(success=True)
    return resp

@app.route('/update/configmaps', methods=['GET', 'POST'])
def configmaps():
    uucppasswd()
    uucpsys()
    newsfeeds()
    newsuucp()
    configmap_uucp = "kubectl create configmap gnuu-uucp --from-file=./passwd --from-file=./sys -o yaml --dry-run=client | kubectl apply -f -".format(result_uucp)
    configmap_news = "kubectl create configmap gnuu-news --from-file=./newsfeeds --from-file=./send-uucp.cf.300 --from-file=./send-uucp.cf.1800 --from-file=./send-uucp.cf.3600 --from-file=./send-uucp.cf.21600 --from-file=./send-uucp.cf.43200 --from-file=./send-uucp.cf.86400 -o yaml --dry-run=client | kubectl apply -f -".format(result_news)
    try:
        result_uucp = subprocess.check_output(
            [configmap_uucp], shell=True)
        result_news = subprocess.check_output(
            [configmap_news], shell=True)
    except subprocess.CalledProcessError as e:
        return "An error occurred while trying to fetch task status updates."
    return 'UUCP %s, News %s' % (result_uucp, result_news)


if __name__ == '__main__':

  app.run(
    host = "0.0.0.0",
    port = 5000,
    debug = 1
  )
