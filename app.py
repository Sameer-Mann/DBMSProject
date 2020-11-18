from flask import Flask, session,request,render_template,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config['FLASK_ENV']='development'
app.config['SESSION_TYPE']='filesystem'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:rmoqaece123@localhost:3306/bookmgm'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=True
Session(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if session.get("user_id") is None:
			return redirect("/login")
		return f(*args, **kwargs)
	return decorated_function

def admin_login(f):
	@wraps(f)
	def g(*args,**kwargs):
		if session.get('admin_id')==None:
			return redirect('/login_admin')
		return f(*args,**kwargs)
	return g

@app.route('/login',methods=['GET','POST'])
def login():
	if request.method=='GET':
		return render_template('login.html',login=True,title='login')

	if request.method=='POST':
		data=request.form
		q = db.session.execute('SELECT id,username,password,isstudent FROM users WHERE username = :u',{'u':data['name']}).fetchone()
		if q is None or (not check_password_hash(q.password,data['password'])):
			return render_template('error.html',msg='Invalid Username/password')

		else:
			session['user_id']=q['id']
			session['student']=q['isstudent']
			session['name']=data['name']
			return redirect(url_for('index'))

@app.route('/register',methods=['GET','POST'])
def register():
	if request.method=='GET':
		return render_template('login.html',register=True,title='Register')

	if request.method=='POST':
		data=request.form
		std=1;
		if(data.get('isStudent') is None):
			std=0;
		if data['email'] is None or data['mobile_no'] is None or data['name'] is None:
			return render_template('error.html',msg='Please fill All The Fields')

		q=db.session.execute('SELECT username FROM users WHERE username= :u',{'u':data['name']}).fetchone()
		if q is not None:
			return render_template('error.html',msg='Username already exists')

		if data['password']!=data['confirm']:
			return render_template('error.html',msg='Both passwords do not match')

		db.session.execute('INSERT INTO users(username,email,mobile_no,password,isstudent) VALUES (:usr,:mail,:mob,:pass,:std)',{"usr":data['name'],"mail":data['email'],"mob":data['mobile_no'],"pass":generate_password_hash(data['password']),"std":(std)})
		db.session.commit()
		return redirect('/login')

@app.route('/logout')
@login_required
def logout():
	session.clear()
	return redirect('/login')

@app.route("/",methods=['GET','POST'])
@login_required
def index():
	if request.method=='GET':
		books=db.session.execute("SELECT * FROM books").fetchall()
		return render_template('index.html',books=books)

	if request.method=='POST':
		query = str(request.form.get('search'))
		if not query.isalnum():
			return render_template('error.html',msg='Invalid Input')

		query='%'+query+'%'
		result = db.session.execute("SELECT * FROM books WHERE isbn LIKE :q OR title LIKE :q OR author LIKE :q OR category LIKE :q",{"q":query})
		results =result.fetchall()
		return render_template('index.html',books=results,cart=False)

@app.route('/review/<bid>',methods=['GET','POST'])
def review(bid):
	if request.method=='GET':
		d = db.session.execute('SELECT * FROM reviews WHERE bid = :bd',{"bd":bid}).fetchall()
		book = db.session.execute('SELECT id,isbn,title,author,copies,price FROM books WHERE id = :bd',{"bd":bid}).fetchone()
		fl = db.session.execute('SELECT * FROM reviews WHERE uid = :ud AND bid = :bd',{"ud":session['user_id'],"bd":bid}).fetchone()
		print(fl)
		if fl is not None:
			disable=True
		else:
			disable=False
		reviews = []
		for x in d:
			name = db.session.execute('SELECT username FROM users WHERE id = :i',{"i":x.uid}).fetchone()
			reviews.append([name,x.review])
		return render_template('book.html',reviews=reviews,book=book,disable=disable)
	if request.method=='POST':
		data = request.form.get('review')
		#book = db.session.execute('SELECT id,isbn,title,author,copies,price FROM books WHERE id = :bd',{"bd":bid}).fetchone()
		if len(data)>100:
			return render_template('error.html',msg='Length must be less than or equal to 100')
		if data == "":
			return render_template('error.html',msg='Review cannot be empty')
		db.session.execute('INSERT INTO reviews(uid,bid,review) VALUES (:ud,:bd,:rv)',{"ud":session['user_id'],"bd":bid,"rv":data})
		db.session.commit()
		return redirect(f'/review/{bid}')
@app.route('/buy/',methods=['POST'])
@login_required
def buy():
	if request.method=='POST':
		copies = request.args.get('copies')
		bid = request.args.get('book_id')
		if copies==0:
			return redirect('/')

		db.session.execute('UPDATE books SET copies = :cp WHERE id = :id',{"cp":int(copies)-1,"id":bid})
		db.session.execute('INSERT INTO cart(uid,bid) VALUES (:ud,:bd)',{"ud":session['user_id'],"bd":bid})
		db.session.commit()
		return redirect('/')

@app.route("/cart",methods=['GET'])
@login_required
def cart():
	if request.method=='GET':
		result=db.session.execute('SELECT bid FROM cart WHERE uid = :q',{'q':session['user_id']}).fetchall()
		results=[]
		for b in result:
			results.append(db.session.execute('SELECT title,author,price FROM books WHERE id = :q',{'q':b.bid}).fetchone())
		return render_template('index.html',cart=True,books=results)

@app.route("/rent/",methods=['GET','POST'])
@login_required
def rent():
	if request.method=='GET':
		res=db.session.execute('SELECT bid FROM rents WHERE uid = :ud',{"ud":session['user_id']}).fetchall()
		results=[]
		for b in res:
			results.append(db.session.execute('SELECT title,author,price,id,copies FROM books WHERE id = :q',{'q':b.bid}).fetchone())
		return render_template('index.html',cart=True,rent=True,books=results)

	if request.method=='POST':
		issued=bool(request.args.get('issued',False))
		bid,copies=request.args.get('book_id'),request.args.get('copies')
		if issued:
			if copies==0:
				return redirect('/')
			db.session.execute('INSERT INTO rents(uid,bid) VALUES (:ud,:bd)',{"ud":session['user_id'],"bd":bid})
			db.session.execute('UPDATE books SET copies = :cp WHERE id = :bd',{"bd":bid,"cp":int(copies)-1})
		else:
			db.session.execute('DELETE FROM rents WHERE uid = :ud AND bid = :bd LIMIT :x',{"ud":session['user_id'],"bd":bid,"x":1})
			db.session.execute('UPDATE books SET copies = :cp WHERE id = :bd',{"cp":int(copies)+1,"bd":bid})
		db.session.commit()
		return redirect('/')

@app.route("/login_admin",methods=['GET','POST'])
def login_admin():
	if request.method=='GET':
		return render_template('admin.html',login=True)
	if request.method=='POST':
		data=request.form
		q = db.session.execute('SELECT id,username,password FROM admins WHERE username = :u',{'u':data['name']}).fetchone()
		if q is None or (not check_password_hash(q.password,data['password'])):
			return render_template('error.html',msg='Invalid Username/password')

		else:
			session['admin_id']=q['id']
			session['admin_user']=data['name']
			books=db.session.execute("SELECT * FROM books").fetchall()
			return render_template('admin.html',books=books,login=False,register=False)

@app.route("/register_admin",methods=['GET','POST'])
#@admin_login
def register_admin():
	if request.method=='GET':
		return render_template('admin.html',register=True)

	if request.method=='POST':
		data=request.form
		if data['email'] is None or data['mobile_no'] is None or data['name'] is None:
			return render_template('error.html',msg='Please fill All The Fields')

		q=db.session.execute('SELECT username FROM admins WHERE username = :u',{'u':data['name']}).fetchone()

		if q is not None:
			return render_template('error.html',msg='Username already exists')

		if data['password']!=data['confirm']:
			return render_template('error.html',msg='Both passwords do not match')

		db.session.execute('INSERT INTO admins(username,email,mobile_no,password) VALUES (:usr,:mail,:mob,:pass)',{"usr":data['name'],"mail":data['email'],"mob":data['mobile_no'],"pass":generate_password_hash(data['password'])})
		db.session.commit()
		return redirect('/admin/books')

@app.route('/logout_admin')
@admin_login
def logout_admin():
	session.clear()
	return redirect('/login_admin')

@app.route("/admin/<tp>",methods=['GET','POST'])
@admin_login
def admin(tp):
	if request.method=='GET':
		if tp=='books':
			books=db.session.execute("SELECT * FROM books").fetchall()
			return render_template('admin.html',books=books,login=False,register=False)

		elif tp=='add_book':
			return render_template('add_book.html')

		elif tp=='issue_status':
			data = db.session.execute('SELECT * FROM rents').fetchall()
			issues=[]
			ct=0
			for i in data:
				bookname=db.session.execute('SELECT title FROM books WHERE id = :id',{'id':i.bid}).fetchone().title
				username=db.session.execute('SELECT username FROM users WHERE id = :id',{'id':i.uid}).fetchone().username
				ct += 1
				issues.append([ct,username,bookname])
			return render_template('admin.html',login=False,register=False,issues=issues)

	if request.method=='POST':
		if tp =='add_book':
			data=request.form
			db.session.execute('INSERT INTO books(title,author,description,category,copies,price,isbn) VALUES (:t,:auth,:des,:cat,:cp,:p,:is)',{"t":data['title'],"auth":data['author'],"des":data['description'],"cat":data['category'],"cp":int(data['copies']),"p":int(data['price']),"is":data["isbn"]})
			db.session.commit()
			return redirect('/admin/books')

		elif tp=='search':
			query = str(request.form.get('search'))
			query='%'+query+'%'
			result = db.session.execute("SELECT * FROM books WHERE isbn LIKE :q OR title LIKE :q OR author LIKE :q OR category LIKE :q",{"q":query})
			results =result.fetchall()
			return render_template('admin.html',books=results,login=False,register=False)

		elif tp=='remove_book':
			bid=int(request.args.get('book_id'))
			db.session.execute('DELETE FROM books WHERE id = :bd',{"bd":bid})
			db.session.commit()
			return redirect('/admin/books')
if __name__ == '__main__':
	app.run(debug=True)