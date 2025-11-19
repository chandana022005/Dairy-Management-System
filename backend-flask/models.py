from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'user', name='role_enum'), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    phone = db.Column(db.String(15), unique=True, nullable=True)

    customers = db.relationship('Customer', backref='user', cascade="all, delete")

    def __repr__(self):
        return f"<User {self.email}>"

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    milk_records = db.relationship('MilkCollection', backref='customer', cascade="all, delete")
    payments = db.relationship('Payment', backref='customer', cascade="all, delete")

class MilkCollection(db.Model):
    __tablename__ = 'milk_collection'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    date = db.Column(db.Date)
    quantity = db.Column(db.Float)
    fat = db.Column(db.Float)
    price_per_litre = db.Column(db.Float)
    total_price = db.Column(db.Float)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    amount_paid = db.Column(db.Float)
    date = db.Column(db.Date)
    payment_mode = db.Column(db.Enum('cash', 'upi', 'bank'), default='cash')

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer, default=0)
