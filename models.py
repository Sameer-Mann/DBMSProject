from flask_sqlalchemy import SQLAlchemy

from app import app
db = SQLAlchemy(app)

class Users(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile_no=db.Column(db.String(13),unique=True,nullable=False)
    isstudent=db.Column(db.Boolean)
    password=db.Column(db.String(100))

    def __repr__(self):
        return f'{self.username}-{self.email}--{self.mobile_no}'

class Books(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    isbn=db.Column(db.String(20),nullable=False)
    title=db.Column(db.String(40),nullable=False)
    author=db.Column(db.String(30),nullable=False)
    description=db.Column(db.String(500))
    category=db.Column(db.String(20),nullable=False)
    copies=db.Column(db.Integer,nullable=False)
    price=db.Column(db.Integer)

    def __repr__(self):
        return f"{self.title} by {self.author} category {self.category}"

class reviews(db.Model):
    uid=db.Column(db.Integer,db.ForeignKey(Users.id),primary_key=True)
    bid=db.Column(db.Integer,db.ForeignKey(Books.id))
    review=db.Column(db.String(100),nullable=False)

    def __repr__(self):
        return f"{self.review} by {self.by_user.username}"

class rents(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    bid=db.Column(db.Integer,db.ForeignKey(Books.id))
    uid=db.Column(db.Integer,db.ForeignKey(Users.id))

    def __repr__(self):
        return f"{self.bid.title} rented by {self.uid.username}"

class admins(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(40), unique=True, nullable=False)
    email=db.Column(db.String(120), unique=True, nullable=False)
    mobile_no=db.Column(db.String(13),unique=True,nullable=False)
    password=db.Column(db.String(100))

    def __repr__(self):
        return f'{self.username}-{self.email}--{self.mobile_no}'

class cart(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    bid=db.Column(db.Integer,db.ForeignKey(Books.id),nullable=False)
    uid=db.Column(db.Integer,db.ForeignKey(Users.id),nullable=False)
x = admins(username="ritik",email="ritik@gmail.com",mobile_no="123234",password=generate_password_hash("ritik"))