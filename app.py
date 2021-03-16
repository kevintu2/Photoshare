######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
from datetime import date
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '5Xbmep7olqrLuc!'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')
@app.route('/add', methods=['POST'])
@flask_login.login_required
def add_friend():
	try:
		email=request.form.get('email')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('add'))
	if((email,) in getUserList()):
		current_user_id = getUserIdFromEmail(flask_login.current_user.id)
		friend_id = getUserIdFromEmail(email)
		cursor = conn.cursor()
		if current_user_id != friend_id:
			print(cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(current_user_id, friend_id)))
			conn.commit()
			return render_template('add.html', message='Friend Added!')
		else:
	 		print("couldn't find all tokens")
	 		return flask.redirect(flask.url_for('add'))
	else:
		return render_template('add.html', message='Friend does not exist')
@app.route('/add', methods=['GET'])
@flask_login.login_required
def add():
	return render_template('add.html')

@app.route('/search', methods=['POST'])
@flask_login.login_required
def searchFriends():
	try:
		first_name=request.form.get('firstname')
		last_name=request.form.get('lastname')
	except:
		print ("couldn't find all tokens")
		return flask.redirect(flask.url_for('friends'))
	cursor = conn.cursor()
	cursor.execute("SELECT email, first_name, last_name, hometown, gender FROM Users WHERE first_name = '{0}' AND last_name = '{1}'".format(first_name, last_name))
	userlist = cursor.fetchall()
	print(first_name)
	print(last_name)
	print(userlist)
	return render_template('search.html', name=flask_login.current_user.id, message='Search Result', result=userlist)

@app.route('/search', methods=['GET'])
@flask_login.login_required
def search():
	return render_template('search.html')

@app.route('/flist', methods=['GET'])
@flask_login.login_required
def friendlist():
	current_userid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name, email FROM Users AS U WHERE U.user_id IN (SELECT DISTINCT user_id2 FROM Friends as F2 WHERE F2.user_id1 = '{0}')".format(current_userid))
	friendlist = cursor.fetchall()
	print(friendlist)
	return render_template('hello.html', name = flask_login.current_user.id, message = 'Friends List', friends = friendlist)

@app.route("/register", methods=['POST'])
def register_user():
	try:
		first_name=request.form.get('firstname')
		last_name=request.form.get('lastname')
		email=request.form.get('email')
		birth_date=request.form.get('birthday')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
		password=request.form.get('password')

	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (first_name, last_name, email, birth_date, hometown, gender, password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(first_name, last_name, email, birth_date, hometown, gender, password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('error'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos=getUsersPhotos(getUserIdFromEmail(flask_login.current_user.id)),base64=base64, albums=getUserAlbums(getUserIdFromEmail(flask_login.current_user.id)))

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def albumBelongToUser(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM Albums WHERE Albums.user_id = '{0}'".format(user_id))
	return cursor.fetchall()

def findAlbumId(name):
	cursor = conn.cursor()
	cursor.execute("SELECT albums_id FROM Albums WHERE Albums.name = '{0}'".format(name))
	return cursor.fetchone()[0]

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		try:
			albums_name = request.form.get('albumname')
			tags = request.form.get('tags')
			tag_list = tags.split(' ')
		except:
			print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
			return flask.redirect(flask.url_for('album'))
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		data =imgfile.read()
		if((albums_name,) in albumBelongToUser(user_id)):
			albums_id = findAlbumId(albums_name)
			cursor = conn.cursor()
			cursor.execute('''INSERT INTO Photos (caption, data, albums_id, user_id) VALUES (%s, %s, %s, %s)''',(caption, data, int(albums_id), int(user_id)))
			conn.commit()

			pid = getPhotoId(caption, data, albums_id)
			cursor = conn.cursor()
			for x in range(len(tag_list)):
				if tagNoExists(tag_list[x]):
					cursor.execute("INSERT INTO Tags (name) VALUES ('{0}')".format(tag_list[x]))
					cursor.execute("INSERT INTO Tagged (photo_id, tag_id) VALUES ('{0}', '{1}')".format(pid, getTagId(tag_list[x])))
				
				else: 
					cursor.execute("INSERT INTO Tagged (photo_id, tag_id) VALUES ('{0}', '{1}')".format(pid, getTagId(tag_list[x])))
			conn.commit()

			return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(user_id),base64=base64)
		else:
			return render_template('hello.html', message='The Album you have selected is not valid')
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code

def getTagId(name):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM Tags WHERE name = '{0}'".format(name))
	return cursor.fetchone()[0]

def tagNoExists(name):
	cursor = conn.cursor()
	if cursor.execute("SELECT name FROM Tags WHERE name = '{0}'".format(name)):
		return False
	else:
		return True

def getPhotoId(caption, data, albums_id):
	cursor = conn.cursor()
	cursor.execute("""SELECT photo_id FROM Photos WHERE caption = %s AND data = %s AND albums_id = %s""", (caption, data, int(albums_id)))
	return cursor.fetchone()[0]

@app.route('/album', methods = ['POST'])
@flask_login.login_required
def createAlbum():
	try:
		name = request.form.get('album')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('album'))
	current_date = date.today()
	current_user_id = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Albums (name, date, user_id) VALUES ('{0}', '{1}', '{2}')".format(name, current_date, current_user_id))
	conn.commit()
	return render_template('album.html', name = flask_login.current_user.id, message = 'Album Created!')

@app.route('/removePhoto', methods = ['POST'])
@flask_login.login_required
def removePhoto():
	try: 
		photo_id = request.args.get('pid')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('hello'))
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	print(photo_id)
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Photos WHERE photo_id = '{0}'".format(photo_id))
	conn.commit()
	return render_template('hello.html', message = 'You have deleted the photo!')

@app.route('/removeAlbum', methods = ['POST'])
@flask_login.login_required
def removeAlbum():
	try: 
		albums_id = request.args.get('aid')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('hello'))
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	print(albums_id)
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Albums WHERE albums_id = '{0}'".format(albums_id))
	conn.commit()
	return render_template('hello.html', message = 'You have deleted the album!')


@app.route('/album')
@flask_login.login_required
def album():
	return render_template('album.html')	

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')

@app.route("/error", methods=['GET'])
def error():
	return render_template('error.html', message='ERROR')

def getPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos")
	return cursor.fetchall()

@app.route('/browse', methods=['GET'])
def browsePhotos():
	photo_list =  getPhotos()
	return render_template('browse.html', photos=photo_list,base64=base64) 

@app.route('/browse/<albums_id>', methods=['GET'])
def showAlbumPhotos(albums_id):
	nameOfAlbum = getAlbumName(albums_id)
	photo_list = getPhotosInAlbum(albums_id)
	return render_template('browse.html', albums = photo_list, album_name=nameOfAlbum, base64=base64)


def getAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT albums_id, name, email FROM Albums, Users WHERE Albums.user_id = Users.user_id")
	return cursor.fetchall()

def getUserAlbums(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT albums_id, name FROM Albums WHERE Albums.user_id = '{0}'".format(user_id))
	return cursor.fetchall()

def getAlbumName(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM Albums WHERE Albums.albums_id = '{0}'".format(album_id))
	return cursor.fetchone()[0]

def getPhotosInAlbum(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE Photos.albums_id = '{0}'".format(album_id))
	return cursor.fetchall()

@app.route('/browsealbum', methods=['GET'])
def browseAlbum():
	listAlbum = getAlbums()
	return render_template('browsealbum.html', albums=listAlbum)

def getAllTags():
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Tags")
	return cursor.fetchall()

def getTagName(tag_id):
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM Tags WHERE tag_id = '{0}'".format(tag_id))
	return cursor.fetchone()[0]

@app.route('/browseMyTags', methods=['GET'])
def viewMyTags():
	return render_template('browseMyTags.html',tags=getAllTags())

def getAllPhotosByTag(tag_id):
	cursor = conn.cursor()
	cursor.execute("SELECT photo_id FROM Tagged WHERE tag_id = '{0}'".format(tag_id))
	return cursor.fetchall()

def getUserPhotosByTag(tag_id, user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos AS P WHERE P.user_id = '{1}' AND P.photo_id IN (SELECT T.photo_id FROM Tagged as T WHERE T.tag_id = '{0}')".format(tag_id, user_id))
	return cursor.fetchall()

@app.route('/userTagPhoto/<tag_id>', methods=['GET'])
@flask_login.login_required
def showByTag(tag_id):
	nameOfTag = getTagName(tag_id)
	photo_list = getUserPhotosByTag(tag_id, getUserIdFromEmail(flask_login.current_user.id))
	print(photo_list)
	return render_template('userTagPhoto.html', photos = photo_list, base64=base64, tag_name=getTagName(tag_id))


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
