from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
# from data import Citys
from flask_mysqldb import MySQL
from pandas.io.json import json_normalize
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
import numpy as np
import datetime

import json
import urllib.request

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)


# Citys = Citys()

# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# Citys
@app.route('/citys')
def citys():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get citys
    result = cur.execute("SELECT * FROM citys")

    citys = cur.fetchall()

    if result > 0:
        return render_template('citys.html', citys=citys)
    else:
        msg = 'No Citys Found'
        return render_template('citys.html', msg=msg)
    # Close connection
    cur.close()


# Single City
@app.route('/city/<string:id>/')
def city(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get city
    result = cur.execute("SELECT * FROM citys WHERE id = %s", [id])

    city = cur.fetchone()

    from geopy.geocoders import Nominatim
    address = city['title']
    geolocator = Nominatim(user_agent="Your_Name")
    location = geolocator.geocode(address)
    print((location.latitude, location.longitude))

    with urllib.request.urlopen(
            "http://api.openweathermap.org/data/2.5/forecast/?lat=52.2297&lon=21.0122&units=metric&appid=ce36b67d60e16d696a162ca68027ee1d") as url:
        dictionary = json.load(url)

        temp = []
        feels_like = []
        temp_min = []
        temp_max = []

        for a in dictionary['list']:
            temp.append(a['main']['temp'])

        for a in dictionary['list']:
            feels_like.append(a['main']['feels_like'])

        for a in dictionary['list']:
            temp_min.append(a['main']['temp_min'])

        for a in dictionary['list']:
            temp_max.append(a['main']['temp_max'])

        print(temp)
        print(feels_like)
        print(temp_min)
        print(temp_max)

        date = []

        for a in dictionary['list']:
            date.append(a['dt_txt'])

        print(date)

        fig, ax, = plt.subplots(figsize=(15, 10))

        ax.plot(temp, color='g')

        ticks = [*range(0, 40)]
        labels = date
        plt.xticks(ticks, labels)
        plt.xticks(rotation=90)

        plt.title("Temperatura w " + address +"\n", fontdict={'fontsize': 20})
        plt.xlabel('\nData i godzina', fontdict={'fontsize': 20})
        plt.ylabel('Temperatura [\N{DEGREE SIGN}C]\n', fontdict={'fontsize': 20})

        plt.gcf()
        chart1path = "C:/Users/Marek/Desktop/Projekt_studia_python/FlaskApp/static/" + address + "chart1.png"
        chart2path = "/static/" + address + "chart1.png"
        plt.savefig(chart1path)
       # plt.show()








    return render_template('city.html', city=city, la=location.latitude, lo=location.longitude, chart=chart2path)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",
                    (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))

    return wrap


# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get citys
    # result = cur.execute("SELECT * FROM citys")
    # Show citys only from the user logged in 
    result = cur.execute("SELECT * FROM citys WHERE author = %s", [session['username']])

    citys = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', citys=citys)
    else:
        msg = 'No Citys Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()


# City Form Class
class CityForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])


# Add City
@app.route('/add_city', methods=['GET', 'POST'])
@is_logged_in
def add_city():
    form = CityForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO citys(title, author) VALUES(%s, %s)", (title, session['username']))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('City Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_city.html', form=form)


# Edit City
@app.route('/edit_city/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_city(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get city by id
    result = cur.execute("SELECT * FROM citys WHERE id = %s", [id])

    city = cur.fetchone()
    cur.close()
    # Get form
    form = CityForm(request.form)

    # Populate city form fields
    form.title.data = city['title']

    if request.method == 'POST' and form.validate():
        title = request.form['title']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute("UPDATE citys SET title=%s WHERE id=%s", (title, id))
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('City Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_city.html', form=form)


# Delete City
@app.route('/delete_city/<string:id>', methods=['POST'])
@is_logged_in
def delete_city(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM citys WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('City Deleted', 'success')

    return redirect(url_for('dashboard'))


# @app.route('/dash', methods = ['GET', 'POST'])
# def dash():
#     if request.method == 'POST':
#         variable = request.form['variable']
#         # data = pd.read_csv("C:/Users/Marek/Desktop/Projekt_studia_python/FlaskApp/static/Crushers.csv")
#
#         columns = ['age', 'week', 'opp', 'ACscr', 'OPPscr', 'location']
#         df = pd.read_csv('C:/Users/Marek/Desktop/Projekt_studia_python/FlaskApp/static/Crushers.csv', names=columns)
#
#         # This you can change it to whatever you want to get
#         age_15 = df[df['age'] == 'U15']
#         # Other examples:
#         bye = df[df['opp'] == 'Bye']
#         crushed_team = df[df['ACscr'] == '0']
#         crushed_visitor = df[df['OPPscr'] == '0']
#         # Play with this
#
#         # Use the .to_html() to get your table in html
#         print(crushed_visitor.to_html())
#
#         return render_template('img.html', chart=crushed_visitor.to_html())
#
#     return render_template('dash.html')

@app.route('/dash', methods=['GET', 'POST'])
def dash():
    if request.method == 'POST':
        variable = request.form['variable']
        # data = pd.read_csv("C:/Users/Marek/Desktop/Projekt_studia_python/FlaskApp/static/Crushers.csv")

        with urllib.request.urlopen(
                "http://api.openweathermap.org/data/2.5/find?q=Palo+Alto&units=metrics&type=accurate&mode=csv&APPID=7d5accb7446c447a519bf74d18da15bb") as url:
            output = json.load(url)

            import matplotlib.pyplot as plt

            dictionary = json.load(open("C:/Users/Marek/Desktop/Projekt_studia_python/FlaskApp/static/file.json", 'r'))
            xAxis = [key for key, value in dictionary.items()]
            yAxis = [value for key, value in dictionary.items()]
            plt.grid(True)

            ## LINE GRAPH ##
            plt.plot(xAxis, yAxis, color='maroon', marker='o')
            plt.xlabel('variable')
            plt.ylabel('value')

            ## BAR GRAPH ##
            fig = plt.figure()
            plt.bar(xAxis, yAxis, color='maroon')
            plt.xlabel('variable')
            plt.ylabel('value')
            fig.savefig("C:/Users/Marek/Desktop/Projekt_studia_python/FlaskApp/static/fig.png")

            plt.show()

            with urllib.request.urlopen(
                    "http://api.openweathermap.org/data/2.5/find?q=Palo+Alto&units=metrics&type=accurate&mode=csv&APPID=7d5accb7446c447a519bf74d18da15bb") as url:
                output = json.load(url)

        return render_template('img.html', chart="/static/fig.png", json=output)

    return render_template('dash.html')


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
