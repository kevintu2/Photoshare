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
app.config['MYSQL_DATABASE_PASSWORD'] = '130Barnes'
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

@app.route('/searchTags', methods = ['POST'])

def searchBy():
	try:

		tags = request.form.get('tags')
		tag_list = tags.split(' ')

	except:

		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('searchTags'))
	resultList = []
	photo_id_by_tags = []
	for x in tag_list:
		try:
			tuplephotolist = getAllPhotosByTag(getTagId(x))
			print('SUCESS')
		except:
			return render_template('searchTags.html', message='The Tag does not Exist')
		photo_id_per_tag = []
		for i in range(len(tuplephotolist)):
			photo_id_per_tag.append(tuplephotolist[i][1])
		photo_id_by_tags.append(photo_id_per_tag)
	
	first_tag_photos = photo_id_by_tags[0]
	rest_tag_photos = photo_id_by_tags[1:len(photo_id_by_tags)]
	for i in first_tag_photos:
		valid = True
		for j in rest_tag_photos:
			if(photoExistInList(i,j)):
				continue
			else:
				valid = False
				break
		if(valid == True):
			resultList.append(i)
		else:
			continue
	photoList = []
	for x in resultList:
		cursor = conn.cursor()
		cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE photo_id = '{0}'".format(x))
		temp = cursor.fetchall()
		photoList.append(temp[0])
	print(photoList)
	return render_template('searchTags.html', message = 'Search Result', result = photoList, base64=base64)


def photoExistInList(photo_id, listOfPhotos):
	if(photo_id in listOfPhotos):
		return True
	else:
		return False
	

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

@app.route('/searchTags' , methods = ['GET'])
def searchtag():
	return render_template('searchTags.html')

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
	cursor.execute("SELECT data, photo_id, caption FROM Photos AS P WHERE P.photo_id IN (SELECT T.photo_id FROM Tagged as T WHERE T.tag_id = '{0}')".format(tag_id))
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
	return render_template('userTagPhoto.html', photos = photo_list, base64=base64, tag_name=nameOfTag)

@app.route('/browseAllTags', methods = ['GET'])
def viewAllTags():
	return render_template('browseAllTags.html', tags = getAllTags())

@app.route('/allTagPhoto/<tag_id>', methods=['GET'])
def showAllByTag(tag_id):
	nameOfTag = getTagName(tag_id)
	photo_list = getAllPhotosByTag(tag_id)
	return render_template('allTagPhoto.html', photos = photo_list, base64=base64, tag_name=nameOfTag)

@app.route('/popularTags', methods = ['GET'])
def viewTopTags():
	tag = getTopTags()
	taglist = []
	for x in tag:
		temp = (x[0], getTagName(x[0]))
		taglist.append(temp)
	return render_template('popularTags.html', tags = taglist)
	

def getTopTags():
	cursor.execute("SELECT tag_id FROM Tagged AS T, Photos AS P WHERE T.photo_id = P.photo_id GROUP BY T.tag_id order by count(P.photo_id) desc limit 3")
	return cursor.fetchall()

def getOwner(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Photos WHERE photo_id = '{0}'".format(photo_id))
	return cursor.fetchone()[0]

@app.route('/commentPhoto', methods = ['POST'])
def commentPhoto():
	try:
		comment = request.form.get('comment')
		print(comment)
		photo_id = request.args.get('pid')
		print(photo_id)
	
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('hello'))
	photo_owner = getOwner(photo_id)
	print(photo_owner)
	comment_date = date.today()
	try:
		user_id = getUserIdFromEmail(flask_login.current_user.id)
	except:
		user_id = None
	if photo_owner == user_id:
		return render_template('hello.html', message = 'You cannot comment on your own photo!')
	else:
		if(user_id == None):
		
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Comments (photo_id, text, date) VALUES('{0}', '{1}', '{2}')".format(photo_id, comment, comment_date))
			conn.commit()
			return render_template('hello.html', message = 'Comment Posted!')
		else:
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Comments (user_id, photo_id, text, date) VALUES('{0}', '{1}', '{2}', '{3}')".format(user_id, photo_id, comment, comment_date))
			conn.commit()
			return render_template('hello.html', message = 'Comment Posted!')

@app.route('/viewComments/<photo_id>', methods = ['GET'])
def viewComments(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT text, date, comment_id FROM Comments WHERE photo_id = '{0}'".format(photo_id))
	commentList = cursor.fetchall()
	return render_template('viewComments.html', message = 'Comments for the Post', commentList = commentList, photo = getPhotoById(photo_id), base64=base64)

@app.route('/viewComments', methods = ['GET'])
def view():
	return render_template('viewComments.html', message = 'Comments for the Post')

def getPhotoById(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE photo_id = '{0}'".format(photo_id))
	return cursor.fetchall()

@app.route('/likephoto', methods = ['POST'])
@flask_login.login_required
def likephoto():
	try:
		photo_id = request.args.get('pid')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('hello', message = 'error'))
	
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Likes WHERE photo_id = '{0}'".format(photo_id))
	liked_users = cursor.fetchall()
	for x in liked_users:
		if user_id == x[0]:
			return render_template('hello.html', message = 'You can not like a photo twice')
		else:
			continue
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Likes (photo_id, user_id) VALUES ('{0}' , '{1}')".format(photo_id,user_id))
	conn.commit()
	return render_template('hello.html', message = 'You liked the photo!')
@app.route('/viewlikes/<photo_id>', methods = ['GET'])
def viewlikes(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Likes WHERE photo_id = '{0}'".format(photo_id))
	liked_users = cursor.fetchall()
	liked_users_list = []
	for x in liked_users:
		temp = list(x)
		temp.append(getEmailFromId(x[0]))
		res = tuple(temp)
		liked_users_list.append(res)
	return render_template('viewlikes.html', message = 'These are Users who Liked the Photo', userlist = liked_users_list, like_count = len(liked_users))

def getEmailFromId(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(user_id))
	return cursor.fetchone()[0]

@app.route('/searchByComment', methods = ['GET'])
def searchByComment():
	return render_template('searchByComment.html')

@app.route('/searchCommentName', methods = ['POST'])
def searchCommentName():
	try:
		text_comment = request.form.get('text_comment')
		
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('searchByComment'))
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*), user_id FROM Comments WHERE text = '{0}' GROUP BY user_id ORDER BY COUNT(*) DESC".format(text_comment))# count the rows of user after 
	userlist = cursor.fetchall()
	userlistFinal = []
	for x in userlist:
		temp = list(x)
		temp.append(getEmailFromId(x[1]))
		res = tuple(temp)
		userlistFinal.append(res)

	return render_template('searchByComment.html', userlist = userlistFinal)

@app.route('/friendRecs', methods = ['GET'])
def friendRecs():
	cursor = conn.cursor()
	cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	current_friendlist = cursor.fetchall()
	masterList = []
	for x in current_friendlist:
		cursor = conn.cursor()
		cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(x[0])) #gets each of your friend's friendlist
		friendlist = cursor.fetchall()
		masterList.append(friendlist)
	mydict = {}
	for i in range(len(masterList)):
		for j in range(len(masterList[i])):
			name = masterList[i][j][0]
			if name in mydict:
				mydict.update({name:(mydict.get(masterList[i][j][0]) + 1)})
			else:
				mydict[name] = 1
	mutual = []
	for key in mydict:
		if mydict.get(key) >= 2:
			mutual.append([key,mydict.get(key)])
	mutual.sort(key=myFunc)
	mutual.reverse()
	for x in mutual:
		if((x[0],) in current_friendlist):
			mutual.remove(x)
	for x in mutual:
		x[0] = getEmailFromId(x[0])
	return render_template('friendRecs.html', mutual_list = mutual, message = 'Here are your friend recommendations')

	
def myFunc(tuple):
	return tuple[1]
	
def getPopular(user_id):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_id FROM Tagged AS T, Photos AS P WHERE T.photo_id = P.photo_id AND P.user_id = '{0}' GROUP BY T.tag_id ORDER BY COUNT(P.photo_id) DESC LIMIT 5".format(user_id)) #grouping tags with count of photos per tag
	return cursor.fetchall()

def getPhotoswithTag(photo_id, name):
	cursor = conn.cursor()
	cursor.execute("SELECT P.photo_id FROM Photos AS P, Tagged AS T WHERE T.photo_id = '{0}' AND T.tag_id ='{1}' AND T.photo_id = P.photo_id".format(photo_id, getTagId(name)))
	return cursor.fetchall()



@app.route('/photoRec', methods = ['GET'])
def photoRec():
	tags = getPopular(getUserIdFromEmail(flask_login.current_user.id))
	tag_list = []
	photo_list = getPhotos()
	mydict = {}
	for x in tags:
		temp = getTagName(x[0])
		tag_list.append(temp)
	for x in photo_list:
		for y in tag_list:
			recList = getPhotoswithTag(x[1],y)
			for photo in recList:
				if(photo[0] in mydict):
					mydict.update({photo[0]: (mydict[photo[0]] + 1)})
				else:
					mydict[photo[0]] = 1
	reclistfinal = sorted(mydict, key=mydict.get, reverse=True)
	listphoto = ()
	for x in reclistfinal:
		cursor = conn.cursor()
		cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE photo_id = '{0}'".format(x))
		listphoto+=(cursor.fetchall())
	print(listphoto)
	return render_template('photoRec.html', message = 'You may also like these photos', photos = listphoto, base64=base64)

def getScore():
	cursor = conn.cursor()
	cursor.execute("SELECT C.user_id, COUNT(user_id) FROM Comments AS C GROUP BY C.user_id")
	scores = []
	scorecomments = cursor.fetchall()
	for x in scorecomments:
		scores.append((x[0], x[1]))
	cursor = conn.cursor()
	cursor.execute("SELECT P.user_id, COUNT(user_id) FROM Photos AS P GROUP BY P.user_id")
	scorephotos = cursor.fetchall()
	finalscore = {}
	for x in scorephotos:
		if getEmailFromId(x[0]) not in finalscore:
			finalscore[getEmailFromId(x[0])] = x[1]
		else:
			finalscore[getEmailFromId(x[0])] += x[1]

	for x in scorecomments:
		if x[0] == None:
			continue
		elif getEmailFromId(x[0]) not in finalscore:
			finalscore[getEmailFromId(x[0])] = x[1]
		else:
			finalscore[getEmailFromId(x[0])] += x[1]

	return finalscore

@app.route('/getRanks', methods = ['GET'])
def getRanks():
	mydict = getScore()
	userlisttemp = sorted(mydict, key=mydict.get, reverse=True)
	userlist=[]
	for i in userlisttemp:
		userlist.append((i,mydict[i]))
	
	if(len(userlist) <= 10):
		return render_template('getRanks.html', message= 'Here are the rankings', ranked = userlist)
	else:
		newranks = []
		for x in range(10):
			newranks.append(userlist[x])
		return render_template('getRanks.html', message = 'Here are the rankings', ranked = newranks)

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
