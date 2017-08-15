# main.py 
from flask import Flask, flash, request, render_template, redirect, session
from math import floor
from sqlite3 import OperationalError
import string, sqlite3
from urllib.parse import urlparse
import sys
import random, string
import os
import requests

host = 'http://localhost:5000/'
hostMask = 'http://cl.ip/'

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return None

def db_check():
    conn = create_connection('urls.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS urls(ID INTEGER PRIMARY KEY,URLKEY VARCHAR(100),URL VARCHAR(100) NOT NULL);")

def newKey():
    uniqueKey = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))
    return uniqueKey
#generate a unique short url
def generateUnique(original_url):
    uniqueKey = newKey()
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM urls WHERE URLKEY = ?", (uniqueKey,))
    data=cursor.fetchone()[0]
    if data==0:
        with sqlite3.connect('urls.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO urls (URL,URLKEY) VALUES ('%s','%s')" %(original_url,uniqueKey))
        return uniqueKey
    else:
        generateUnique(original_url)

#checking to see if long url has existing short url
def checkUnique(url):
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM urls WHERE URL = ?", (url,))
    data=cursor.fetchone()[0]
    if data==0:
        uniqueKey = generateUnique(url)
        return uniqueKey
    else:
        cursor.execute("SELECT URLKEY FROM urls WHERE URL=('%s')"%(url))
        existing_urlkey=cursor.fetchone()[0]
        return existing_urlkey

def validWebsite(url):
    try:
        request = requests.get(url)
        return 1
    except:
        return 0

def getExistingUrlKey(original_url):
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT URLKEY from urls where URL=('%s')"%(original_url))
        existing_urlkey = cursor.fetchone()[0]
    return existing_urlkey

def getExistingUrl(original_url):
    original_url=original_url.replace('http://cl.ip/','').replace('cl.ip/','')
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM urls WHERE URLKEY=('%s')"%(original_url))
        countURL = cursor.fetchone()[0]
    if countURL==0:
        flash("That Unique ID doesn't exist.")
    else:
        cursor.execute("SELECT URL FROM urls WHERE URLKEY=('%s')"%(original_url))
        keyMappedURL = cursor.fetchone()[0]
        return keyMappedURL

app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        original_url = request.form.get('url')
        if 'cl.ip' not in original_url:
            if urlparse(original_url).scheme == '':
                original_url = ('http://'+original_url)
            original_url = original_url.replace('www.','')
            #check if valid website
            if validWebsite(original_url)==1:
                #check if URL is unique & generate OR return existing short URL
                aKey = checkUnique(original_url)
                return render_template('home.html',short_url=host+aKey,mask_url=hostMask+aKey)
            else:
                flash("You have entered an invalid URL.")
        else:
            existing_url = getExistingUrl(original_url)
            return render_template('home.html',short_url=existing_url,mask_url=existing_url)
    return render_template('home.html')

@app.route('/<short_url>')
def doesntmatter(short_url):
    uniqueKey=short_url
    redirect_url = 'http://localhost:5000'
    with sqlite3.connect('urls.db') as conn:
        cursor = conn.cursor()
        result_cursor = cursor.execute("SELECT URL FROM urls WHERE URLKEY=('%s')"%(uniqueKey))
        try:
            redirect_url = result_cursor.fetchone()[0]
        except Exception as e:
            print (e)
    return redirect(redirect_url)

secret_key = os.urandom(24)
app.secret_key=secret_key
if __name__ == '__main__':
    db_check()
    app.run(debug=True)