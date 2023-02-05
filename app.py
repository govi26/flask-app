import re
from flask import Flask, g, render_template, request, redirect, url_for, session
import sqlite3


app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

app.debug = True

def get_db_connection():
  if not hasattr(g, 'db_connection'):
    try:
      g.db_connection = sqlite3.connect('flaskapp_db.sql')
    except Exception as error:
      print(f'Error: {error}')
      raise error
  return g.db_connection

def get_db_cursor():
  try:
    connection = get_db_connection()
  except Exception as error:
    print(f'Error: {error}')
    raise error
  return connection.cursor()

@app.teardown_appcontext
def close_db(error):
  if hasattr(g, 'db_connection'):
      g.db_connection.close()

@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
  msg = ''
  if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
    username = request.form['username']
    password = request.form['password']
    cursor = get_db_cursor()
    cursor.execute('SELECT * FROM user WHERE username=? AND password=?', (username, password))
    account = cursor.fetchone()
    if account:
      session['loggedin'] = True
      session['id'] = account[0]
      session['username'] = account[1]
      return redirect(url_for('dashboard'))
    else:
      msg = 'Incorrect username/password!'
  return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
  session['loggedin'] = False
  session['id'] = None
  session['username'] = None
  return render_template('logout.html')

@app.route('/dashboard')
def dashboard():
  if not session['loggedin']:
    return redirect(url_for('login'))
  cursor = get_db_cursor()
  cursor.execute('SELECT * FROM user WHERE id=?', (session['id'],))
  user = cursor.fetchone()
  return render_template('dashboard.html', user=user)

@app.route('/register', methods =['GET', 'POST'])
def register():
  msg = ''
  if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    cursor = get_db_cursor()
    cursor.execute('SELECT * FROM user WHERE username=?', (username,))
    user = cursor.fetchone()
    if user:
      msg = 'User account already exists!'
    elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
      msg = 'Invalid email address!'
    elif not re.match(r'[A-Za-z0-9]+', username):
      msg = 'Username must contain only characters and numbers!'
    elif not (re.match(r'[A-Za-z]+', first_name) and re.match(r'[A-Za-z]+', last_name)):
      msg = 'First/Last name cannot contain numbers, specials characters!'
    elif not username or not password or not email:
      msg = 'Please fill out the form correctly!'
    else:
      cursor.execute('INSERT INTO user VALUES (NULL, ?, ?, ?, ?, ?)', (username, password, first_name, last_name, email))
      get_db_connection().commit()
      msg = 'You have successfully registered!'
      session['loggedin'] = True
      session['id'] = cursor.lastrowid
      session['username'] = username
      return redirect(url_for('dashboard'))
  elif request.method == 'POST':
    msg = 'Please fill out the form!'
  return render_template('register.html', msg=msg)


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80)