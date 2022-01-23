from flask import Flask, request, jsonify, render_template,Response
import math
import json
from flask import Flask,render_template, flash, redirect , url_for , session ,request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField , TextAreaField ,PasswordField , validators
from passlib.hash import sha256_crypt
from functools import wraps
from mysql.connector import Error
from mysql.connector import pooling


app = Flask(__name__)

# connection_pool = pooling.MySQLConnectionPool(pool_name="pynative_pool",
#                                                 pool_size=5,
#                                                 pool_reset_session=True,
#                                                 host=os.getenv('DB_HOST'),
#                                                 database=os.getenv('DB_NAME'),
#                                                 user=os.getenv('DB_USER'),
#                                                 password=os.getenv('DB_PASSWORD'))

connection_pool = pooling.MySQLConnectionPool(pool_name="pynative_pool",
                                                pool_size=5,
                                                pool_reset_session=True,
                                                host='frazor-testdb.cwowgpm6kuqt.ap-south-1.rds.amazonaws.com',
                                                database='frazordashboard',
                                                user='root',
                                                password='test1234')


class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1,max=50)])
    phone = StringField('Mobile Number',[validators.Length(min=4,max=25)])
    email = StringField('Email',[validators.Length(min=4,max=25)])
    password = PasswordField('Password', [ validators.DataRequired (),validators.EqualTo('confirm',message ='passwords do not match')])
    confirm = PasswordField('Confirm password')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)

    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        phone = form.phone.data
        phone = str(phone)
        password = sha256_crypt.encrypt(str(form.password.data))
        print(phone)
        # Create crusor

        try:
            connection_object = connection_pool.get_connection()
            if connection_object.is_connected():
                cursor = connection_object.cursor()
                cursor.execute("INSERT INTO user_login(email,name,phone,password) VALUES(%s,%s,%s,%s)",(email,name,phone,password))
                connection_object.commit()
                flash("You are now Registered and you can login" , 'success')
                redirect(url_for('login'))
        except Error as e:
            print("Error while connecting to MySQL using Connection pool ", e)
            Response('Ok',status=200)
        finally:
            # closing database connection.
            if connection_object.is_connected():
                cursor.close()
                connection_object.close()
                print("MySQL connection is closed")

    return render_template('register.html',form=form)

@app.route('/login',methods =['GET','POST'])
def login():
    if request.method == 'POST':
        #Get Form Fields
        phone = request.form['phone']
        phone = str(phone)
        password_candidate = request.form['password']

        # Create cursor

        try:
            connection_object = connection_pool.get_connection()
            if connection_object.is_connected():
                cursor = connection_object.cursor()
                cursor.execute("SELECT * FROM user_login WHERE phone = %s" ,[phone])

                count = 0
                for data in cursor.fetchall():
                    # Get Stored hash
                    password = data[5]

                    # Compare Passwords
                    print("bbbbbbbbbbbbbbbb")
                    print(data)
                    count = count + 1
                    if sha256_crypt.verify(password_candidate,password):
                        #Passed
                        session['logged_in'] = True
                        session['phone'] = phone
                        flash('You are now logged in ','success')
                        return redirect(url_for('index'))
                    else:
                        error = 'Username/Password fields are incorrect'
                        return render_template('login.html',error=error)
                if count==0:
                    error = 'Username/Password fields are incorrect'
                    return render_template('login.html',error=error)

        except Error as e:
            print("Error while connecting to MySQL using Connection pool ", e)
            Response('Ok',status=200)
        finally:
            # closing database connection.
            if connection_object.is_connected():
                cursor.close()
                connection_object.close()
                print("MySQL connection is closed")

    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login','danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('you are now logged out ','success')
    return redirect(url_for('home'))



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
@is_logged_in
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.secret_key='secret123'
    app.run(debug=True,port=8000)
