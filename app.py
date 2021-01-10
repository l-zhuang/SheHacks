from flask import Flask,render_template,request, redirect, url_for, flash
from werkzeug.security import check_password_hash,generate_password_hash
from flask_login import UserMixin,LoginManager,login_required,login_user,current_user,logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo
from datetime import datetime


app=Flask(__name__)
app.config['SECRET_KEY']='secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)

# create login manager
login_manager = LoginManager()
login_manager.init_app(app)

#User Database
class User(UserMixin,db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(15), index=True, unique=True)
  email=db.Column(db.String(50),index=True,unique=True)
  password_hash=db.Column(db.String(30))
  logs = db.relationship('Log', backref='book', lazy='dynamic')
  def __repr__(self):
    return '<User {}>'.format(self.username)
  def set_password(self, password):
    self.password_hash = generate_password_hash(password)
  
  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

#Medical Log
class Log(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  bloodL = db.Column(db.Integer, index=True)
  exerciseL=db.Column(db.String(50), index=True)
  user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
  #submitted=db.Column(db.DateTime)
# Create User Table
#db.create_all()

# Assessment form 
class LogForm(FlaskForm):
  blevel=StringField('Blood glucose level',validators=[DataRequired()])
  elevel=StringField('Exercise level',validators=[DataRequired()])
  submit = SubmitField('Request Review by Nurse')
# login form
class LoginForm(FlaskForm):
  email = StringField('Email',validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  remember = BooleanField('Remember Me')
  submit = SubmitField('Login')

# registration form
class RegistrationForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired()])
  email = StringField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
  submit = SubmitField('Register')

@app.route('/')
def index():
    #users = User.query.all()
    return render_template('index.html')

# user loader
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

# Assessment form page
@app.route('/user/<username>/assessment',methods=['Get','POST'])
@login_required
def aform(username):
  lform=LogForm()
  if lform.validate_on_submit():
    user=User.query.filter_by(username=username).first_or_404()
    f=Log(bloodL=lform.blevel.data,exerciseL=lform.elevel.data,user_id=user.id)
    #update log form
    db.session.add(f)
    db.session.commit()
    return redirect(f'/user/{username}/assessment')
  return render_template("assessment.html",form=lform,username=username)


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

# user route
@app.route('/user/<username>')
@login_required
def user(username):
  user = User.query.filter_by(username=username).first_or_404()
  return render_template('user.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
  form = RegistrationForm(csrf_enabled=False)
  if form.validate_on_submit():
    # define user with data from form here:
    user = User(username=form.username.data, email=form.email.data)
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()
  return render_template('register.html', title='Register', form=form)

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