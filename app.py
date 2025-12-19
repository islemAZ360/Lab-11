from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Expense
from datetime import datetime, timedelta
from sqlalchemy import func

from flask_migrate import Migrate

app = Flask(__name__)

# --- Конфигурация базы данных (SQLite) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

migrate = Migrate(app, db)

# Создание таблиц в БД перед первым запросом (если они не существуют)
with app.app_context():
    db.create_all()

# --- Главная страница: Список пользователей и статистика за прошлый месяц ---
@app.route('/')
def index():
    users = User.query.all()
    
    # Вычисление дат для прошлого месяца
    today = datetime.today()
    first_day_current_month = today.replace(day=1)
    last_day_prev_month = first_day_current_month - timedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1)

    users_data = []
    for user in users:
        # SQL запрос для подсчета суммы расходов пользователя за прошлый месяц
        total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user.id,
            Expense.date >= first_day_prev_month,
            Expense.date <= last_day_prev_month
        ).scalar() or 0
        users_data.append({'user': user, 'total_last_month': total})

    return render_template('index.html', users_data=users_data)

# --- Добавление нового пользователя ---
@app.route('/user/add', methods=['POST'])
def add_user():
    name = request.form.get('name')
    if name:
        new_user = User(name=name)
        db.session.add(new_user)
        db.session.commit() # Сохранение изменений в БД
    return redirect(url_for('index'))

# --- Страница расходов пользователя (Просмотр, Фильтрация) ---
@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
def user_expenses(user_id):
    user = User.query.get_or_404(user_id)
    
    # Получение параметров фильтрации из URL
    category_filter = request.args.get('category')
    date_filter = request.args.get('date')
    
    # Базовый запрос: выбрать расходы текущего пользователя
    query = Expense.query.filter_by(user_id=user_id)
    
    # Применение фильтров, если они заданы
    if category_filter:
        query = query.filter(Expense.category.ilike(f"%{category_filter}%"))
    if date_filter:
        date_obj = datetime.strptime(date_filter, '%Y-%m-%d')
        query = query.filter(Expense.date == date_obj)
        
    # Сортировка по дате (сначала новые)
    expenses = query.order_by(Expense.date.desc()).all()
    
    # Статистика: общая сумма отображаемых (отфильтрованных) расходов
    total_shown = sum(e.amount for e in expenses)

    return render_template('user_expenses.html', user=user, expenses=expenses, total=total_shown)

# --- Добавление нового расхода ---
@app.route('/expense/add/<int:user_id>', methods=['GET', 'POST'])
def add_expense(user_id):
    if request.method == 'POST':
        # Получение данных из формы
        category = request.form['category']
        amount = float(request.form['amount'])
        date_str = request.form['date']
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        comment = request.form['comment']
        payment_method = request.form['payment_method']
        
        # Создание объекта расхода и сохранение в БД
        new_expense = Expense(category=category, amount=amount, date=date_obj, 
                              comment=comment, payment_method=payment_method, user_id=user_id)
        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('user_expenses', user_id=user_id))
    
    return render_template('expense_form.html', action="Add", user_id=user_id)

# --- Редактирование существующего расхода ---
@app.route('/expense/edit/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if request.method == 'POST':
        # Обновление полей
        expense.category = request.form['category']
        expense.amount = float(request.form['amount'])
        expense.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        expense.comment = request.form['comment']
        expense.payment_method = request.form['payment_method']
        
        db.session.commit()
        return redirect(url_for('user_expenses', user_id=expense.user_id))
        
    return render_template('expense_form.html', action="Edit", expense=expense, user_id=expense.user_id)

# --- Удаление расхода ---
@app.route('/expense/delete/<int:expense_id>')
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    user_id = expense.user_id
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('user_expenses', user_id=user_id))

# --- Удаление пользователя ---
@app.route('/user/delete/<int:user_id>')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)