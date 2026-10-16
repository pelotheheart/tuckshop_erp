# Django's MySQL support expects a driver called "mysqlclient", which can be a pain
# to install on Windows. PyMySQL does the same job and installs anywhere, so these
# two lines tell Django to use PyMySQL whenever it asks for mysqlclient.
import pymysql

pymysql.install_as_MySQLdb()
