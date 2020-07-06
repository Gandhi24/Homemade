from flask import Flask, render_template, flash, jsonify, request, url_for, \
                  redirect, session, g
from dbconnect import connection
from flask_mysqldb import MySQL
from MySQLdb import escape_string
from wtforms import Form, TextField, PasswordField, BooleanField, validators, TextAreaField, StringField, SelectField
from passlib.hash import sha256_crypt
from functools import wraps
import random
import gc
import os


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=25)])
    email = TextField('Email address', [validators.Length(min=5, max=50)])
    password = PasswordField('Password', [validators.Required(),
                                          validators.EqualTo('confirm',
                                                             message='Passwords must match')])
    confirm = PasswordField('Repeat password')


class RecipeForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    country = SelectField('Country')
    ingredients = TextAreaField('Ingredients', [validators.Length(min=5)])
    recipe = TextAreaField('Recipe', [validators.Length(min=30)])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            username = session['username']
        except KeyError:
            username = None
        if username is None:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function



def convert2HTML(text):
    if ('1.' in text) and ('2.' in text) and ('3.' in text):  # We have a list here
        final = 1
        for line in text.split('\r\n'):
            if line.startswith('%s.' % final):
                final += 1

        newtext = ''
        i = 1
        for line in text.split('\r\n'):
            if line.startswith('%s.' % i):
                if i == 1:
                    newtext += '<ol>\r\n'
                i += 1
                newline = '<li>' + line[2:] + '</li>\r\n'
                newtext += newline
                if i == final:
                    newtext +=  '</ol>'
            else:
                newtext += line + '\r\n'
        return newtext

    else:
        return text


# Setup Flask
app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'piyush'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'homemade'

mysql = MySQL(app)


@app.route('/')
def homepage():
    return render_template('main.html')


@app.route('/login/', methods=['GET', 'POST'])
def login_page():
    try:
        error = None
        conn = mysql.connect           
        c = conn.cursor()
        if request.method == 'POST':
            username = escape_string(request.form['username']).decode()
            data = c.execute('SELECT * FROM users WHERE username = ("%s");' % username)
            data = c.fetchone()
            print(data[0])
            print(username)
            if (data[0] == username):
                print('success')
                session['logged_in'] = True
                session['username'] = username
                return render_template('user.html')
            else:
                error = 'Invalid credentials, try again'
        gc.collect()
        return render_template('login.html', error=error)
    except:
        return render_template('user.html')


@app.route('/logout/')
@login_required
def logout_page():
    if session['logged_in']:
        session['logged_in'] = False
        session['username'] = None
    return redirect(url_for('list_recipes'))


@app.route('/register/', methods=['GET', 'POST'])
def register_page():
    form = RegistrationForm(request.form)
    try:
        if request.method == 'POST' and form.validate():
            username = form.username.data
            email = form.email.data
            password = form.password.data

            c = mysql.connection.cursor()
            x = c.execute('SELECT * FROM users WHERE username = ("%s");' %
                             escape_string(username))
            
            if int(x) > 0:
                flash('That username is already taken, please choose another')
                return render_template('register.html', form=form)
            else:
                cur = mysql.connection.cursor()
                print(username)
                cur.execute("INSERT INTO users VALUES (username, email, password)")
                mysql.connection.commit()
                cur.close()
                flash('Thanks for registering!')
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('favourites_page'))
        return render_template('register.html', form=form)
    except Exception as e:
        return render_template('register.html', form=form)


@app.route('/searchdishes/', methods=['GET', 'POST'])
def searchrecipe():
    if request.method == 'POST':
        dish = request.form['dish']
        # search by author or book
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute("SELECT dish_name, dish_recipe from dishes WHERE dish_name LIKE %s", [dish])
        conn.commit()
        data = cursor.fetchall()
        # all in the search box will return all the tuples
        if len(data) == 0 and dish == 'all': 
            cursor.execute("SELECT title, recipe from dishes")
            conn.commit()
            data = cursor.fetchall()
        return render_template('searchdishes.html', data=data)
        # print request.form
    return render_template('searchdishes.html')




@app.route('/_background/')
def background():
    try:
        i = request.args.get('ingredients_submit', 0, type=str)
        return jsonify(ingredient=i)
    except Error:
        return str(e)

@app.route('/recipes/')
def list_recipes():
    conn = mysql.connect
    c = conn.cursor()
    _ = c.execute('SELECT rid, title FROM recipes;')
    recipes = c.fetchall()
    c.close()
    conn.close()
    gc.collect()
    return render_template('recipes.html', recipes=recipes)



@app.route('/user/')
@login_required
def user_page():
    print('user_page')
    try:
        user = session['username']
        conn = mysql.connect
        c = conn.cursor()
        if user == 'Daniel':
            _ = c.execute('SELECT rid, location, title FROM recipes;')
        else:
            _ = c.execute('SELECT rid, location, title FROM recipes WHERE user="%s";' % user)
        recipes = c.fetchall()
        c.close()
        conn.close()
        gc.collect()

        recipes = [
            {
                'rid': recipe[0],
                'country': recipe[1],
                'title': recipe[2]
             } for recipe in recipes]

        rank = get_ranking()
        if user not in rank.keys():
            number_recipes = 0
        else:
            number_recipes = rank[user]
        total_recipes = sum(rank.values())
        return render_template('user.html', user=user, nr=number_recipes, tr=total_recipes, recipes=recipes)
    except Exception as e:
        return render_template('favourites.html', favourites=False)


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    sess.init_app(app)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
