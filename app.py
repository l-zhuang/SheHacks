from flask import Flask,render_template,request, redirect, url_for, flash
from werkzeug.security import check_password_hash,generate_password_hash
from flask_login import UserMixin,LoginManager,login_required,login_user,current_user,logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo
from datetime import datetime
from os import environ

#Carbs Calculator
import numpy as np
import pandas as pd
#import os

data=pd.read_csv(r"C:\Users\lzhua\OneDrive\Desktop\MedMo\myapp\DataSet\nutrients_csvfile.csv")
data_found=data.loc[data.Food=='Beef']

print(data_found['Carbs'].item())
#print(carb['Calories'][0])


app=Flask(__name__)
app.config['SECRET_KEY']='secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL') or'sqlite:///my_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)

# create login manager
login_manager = LoginManager()
login_manager.init_app(app)

#User Database Table
class User(UserMixin,db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(15), index=True, unique=True)
  email=db.Column(db.String(50),index=True,unique=True)
  password_hash=db.Column(db.String(30))
  logs = db.relationship('Log', backref='user', lazy='dynamic')
  foods = db.relationship('Food', backref='user', lazy='dynamic')
  def __repr__(self):
    return '<User {}>'.format(self.username)
  def set_password(self, password):
    self.password_hash = generate_password_hash(password)
  
  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

#MedicalLog Database Table
class Log(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  bloodL = db.Column(db.Integer, index=True)
  exerciseL=db.Column(db.String(50), index=True)
  user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
  #submitted=db.Column(db.DateTime)

#Nutrition Database Table
class Food(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  foodI=db.Column(db.String(50), index=True)
  size=db.Column(db.Integer, index=True)
  user_id=db.Column(db.Integer,db.ForeignKey('user.id'))


# Create Database Table
db.create_all()

#Calcultion flask form 
class cForm(FlaskForm):
  food=StringField('Enter the food you have today',validators=[DataRequired()])
  size=StringField('Enter the size in g',validators=[DataRequired()])
  submit=SubmitField("Calculate")

# Assessment flask form 
class LogForm(FlaskForm):
  blevel=StringField('Blood glucose level',validators=[DataRequired()])
  elevel=StringField('Exercise level',validators=[DataRequired()])
  submit = SubmitField('Request Review by Nurse')
# Login flask form
class LoginForm(FlaskForm):
  email = StringField('Email',validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember = BooleanField('Remember Me')
  submit = SubmitField('Login')

# Registration flask Form
class RegistrationForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired()])
  email = StringField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
  submit = SubmitField('Register')

#route

#Main page route
@app.route('/')
def index():
    #users = User.query.all()
    return render_template('index.html')

# User loader
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


# Assessment page route
@app.route('/user/<username>/assessment/next',methods=['Get','POST'])
@login_required
def aform(username):
  lform=LogForm()
  if lform.validate_on_submit():
    user=User.query.filter_by(username=username).first_or_404()

    f=Log(bloodL=lform.blevel.data,exerciseL=lform.elevel.data,user_id=user.id)
    #update log form
    db.session.add(f)
    db.session.commit()
    return redirect(f'/user/{username}/assessment/next')
  return render_template("assessment.html",form=lform,username=username)

# Assessment page route
@app.route('/user/<username>/assessment',methods=['Get','POST'])
@login_required
def calform(username):
  cform=cForm()
  if cform.validate_on_submit():
    user=User.query.filter_by(username=username).first_or_404()
    data=pd.read_csv(r"C:\Users\lzhua\OneDrive\Desktop\MedMo\myapp\DataSet\nutrients_csvfile.csv")
    data_found=data.loc[data.Food==cform.food.data]
    value=int((data_found['Carbs']).iloc[0])
    gram=int((data_found['Grams']).iloc[0])
    eValue=int(cform.size.data)
    fV=value/gram*eValue
    f=Food(foodI=cform.food.data,size=eValue,user_id=user.id)
    #update log form
    db.session.add(f)
    db.session.commit()
    return render_template("calculation.html",form=cform,username=username,value=fV,c=True)
  return render_template("calculation.html",form=cform,username=username,c=False)

# Portfolio page route
@app.route('/user/<username>/portfolio',methods=['Get','POST'])
@login_required
def portfolio(username):
  user=User.query.filter_by(username=username).first_or_404()
  logs=Log.query.filter_by(user_id=user.id).all()
  return render_template("portfolio.html",logs=logs,username=username)

# login route
@app.route('/login', methods=['GET','POST'])
def login():
  form = LoginForm(csrf_enabled=False)
  if form.validate_on_submit():
    # query User here:
     user = User.query.filter_by(email=form.email.data).first()
    # check if a user was found and the form password matches here:
     if user and user.check_password(form.password.data):
      # login user here:
      login_user(user, remember=form.remember.data)
      next_page = request.args.get('next')
      return redirect(f'/user/{user.username}') #if next_page else redirect(url_for('index', _external=True, _scheme='http'))
     else:
      return redirect(url_for('login', _external=True, _scheme='http'))
  return render_template('login.html', form=form)

# user main page route
@app.route('/user/<username>')
@login_required
def user(username):
  user = User.query.filter_by(username=username).first_or_404()
  return render_template('user.html', user=user)

#Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
  form = RegistrationForm(csrf_enabled=False)
  if form.validate_on_submit():
    # define user with data from form here:
    submission=True
    user = User(username=form.username.data, email=form.email.data)
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()
  else:
    submission=False
  return render_template('register.html', title='Register', form=form,sub=submission)

#logOut Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index', _external=True, _scheme='http'))

@login_manager.unauthorized_handler
def unauthorized():
  return "You must be logged in to view this page"

@app.errorhandler(404) 
def not_found(e): 
  return render_template("404.html") 