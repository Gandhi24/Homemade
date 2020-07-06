from flask_mysqldb import MySQL
try:
    import urlparse
except ModuleNotFoundError:
    from urllib import parse as urlparse
import os

def connection():
    conn = MySQL.connect(host='127.0.0.1',
                           user='piyush',
                           passwd='1234',
                           db='homemade'
                           )
    c = conn.cursor()
    return c, conn
