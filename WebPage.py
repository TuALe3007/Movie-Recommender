import csv

from flask import Flask, render_template, session, make_response, request, redirect, url_for
from DataProcessor import DataProcessor
from SQLHandler import *
import time

# Flask instructions found on https://flask.palletsprojects.com/en/2.2.x/tutorial/
app = Flask(__name__)
app.secret_key = 'ca11d96aae1fba4457385e36931f3f9eee4f28b02999681f8c7dc56953e7f9b2'
data = DataProcessor()
handler = SQLHandler()

# Reload page to get new reviews
@app.route('/reload')
def reload():
    global data
    data = DataProcessor()
    return redirect('/home')

# Login page
@app.route('/login', methods=('GET', 'POST'))
def login():
    if not session.keys().__contains__('username'):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            print(username + " " + password)
            log_in = handler.authenticateUser(username, password)
            if not log_in:
                return redirect('/login')
            else:
                session['username'] = username
                userid = int(handler.getUserId(username)[0]) + 162541
                session['userid'] = str(userid)
                return redirect('/home')
    else:
        return redirect('/home')
    return render_template('login.html')

# Register page
@app.route('/register', methods=('GET', 'POST'))
def register():
    if not session.keys().__contains__('username'):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            print(username + " " + password)
            registered = handler.registerUser(username, password)
            if not registered:
                return redirect('/register')
            else:
                return redirect('/login')
    else:
        return redirect('/home')
    return render_template('register.html')

# Home page
@app.route('/home')
def home():
    if session['username'] is None:
        return redirect('/login')
    userid = int(session['userid'])
    recommendation = data.recommend_userId([userid])[0:20]
    movies = data.movies
    posters = data.movie_posters

    # Getting recommendations for the user
    # If the user is new (no ratings) then returns the most popular movies
    rec = []
    rec_title = []
    for i in recommendation:
        to_add = posters[posters['movieId'] == i]['imageURL'].values
        title_to_add = movies[movies['movieId'] == i].get('title').values
        if len(to_add) >= 1:
            rec.append(to_add[0])
            rec_title.append(title_to_add[0])

    # Getting the most popular movies
    popular = []
    pop_title = []
    for p in range(20):
        temp_id = data.popular_movies['movieId'].head(20).values[p]
        temp = posters[posters['movieId'] == temp_id]['imageURL'].values
        title_to_add = movies[movies['movieId'] == temp_id].get('title').values
        if len(temp) >= 1:
            popular.append(temp[0])
            pop_title.append(title_to_add[0])

    # Rendering the HTML page
    return render_template('home.html', recs=rec, len_r=len(rec), user=session['username'], posters=posters,
                           pop=popular, len_p=len(popular), rec_title=rec_title, pop_title=pop_title)

# Add rating page
@app.route('/addRating', methods=('GET', 'POST'))
def addComment():
    if request.method == 'POST':
        title = request.form['movieName']
        # If movie name is incorrect, redirect back
        if title not in data.movies['title'].values:
            print('Movie name does not exist')
            return redirect('/addRating')

        # Else get all the info and print them to the movie file
        to_add = []
        rating = float(request.form['rating'])
        cur_time = int(time.time())
        userid = int(session['userid'])
        movie_id = data.movies['movieId'][data.movies.title == title].values.tolist()[0]
        rating_info = [userid, movie_id, rating, cur_time]
        to_add.append(rating_info)
        print(to_add)

        file = open('ratings-short.csv', "a")
        for info in to_add:
            writer = csv.writer(file)
            writer.writerow(info)
        file.close()

        return redirect('/home')
    return render_template('addRating.html')

# Group recommendation page
@app.route('/groupRecommendation', methods=('GET', 'POST'))
def groupRecommendation():
    if request.method == 'GET':
        users = handler.getAllUsers()
        # Removed the currently logged in user
        for user in users:
            if user == session['username']:
                users.remove(user)
        return render_template('groupRecommendation.html', users=users, current=session['username'])
    elif request.method == 'POST':
        checked_users = [session['user_id']]
        for x in request.form.keys():
            checked_userid = int(handler.getUserId(x)[0]) + 162541
            checked_users.append(str(checked_userid))

        recommendation = data.recommend_userId(checked_users)[0:20]
        posters = data.movie_posters
        movies = data.movies
        rec = []
        rec_title = []
        for i in recommendation:
            to_add = posters[posters['movieId'] == i]['imageURL'].values
            title_to_add = movies[movies['movieId'] == i]['title'].values
            if len(to_add) >= 1:
                rec.append(to_add[0])
                rec_title.append(title_to_add[0])
        return render_template('groupRecommendation.html', current=session['username'], recs=rec, len_r=len(rec),
                               rec_title=rec_title)

# Logout button
@app.route('/logout')
def logout():
    # remove the username and userid from the session
    session.pop('username', None)
    session.pop('userid', None)
    return redirect('/login')
