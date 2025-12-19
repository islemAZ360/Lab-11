from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """Сущность Пользователь"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Связь с таблицей расходов (One-to-Many relationship)
    # cascade="all, delete" удаляет все расходы пользователя при удалении самого пользователя
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade="all, delete")

class Expense(db.Model):
    """Сущность Расход"""
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False) # Категория (еда, транспорт и т.д.)
    amount = db.Column(db.Float, nullable=False)        # Сумма расхода
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow) # Дата
    comment = db.Column(db.String(200))                 # Комментарий
    payment_method = db.Column(db.String(50))           # Способ оплаты (наличные, карта)
    
    # Внешний ключ для связи с пользователем
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)