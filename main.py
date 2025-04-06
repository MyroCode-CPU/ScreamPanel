import os
import sqlite3
import bcrypt
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from models import db, User  # импортируем db и User из models
import hashlib
import time

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hhjguafhsdyguyhduashfudshfuhdfguhdfghg'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myro_panel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()  # ← создаёт таблицы, если они не существуют
    
app.secret_key = 'bhqyhgyfhughjfgjgjgoijfsdoi'  # Измени на свой ключ

# Функция подключения к БД
def get_db_connection():
    conn = sqlite3.connect('myro_panel.db')
    conn.row_factory = sqlite3.Row
    return conn
def generate_token(user_key, serial):
    raw = f'PUBG-{user_key}-{serial}-Vm8Lk7Uj2JmsjCPVPVjrLa7zgfx3uz9E'
    return hashlib.md5(raw.encode()).hexdigest()
@app.route('/connect', methods=['POST'])
def connect():
    user_key = request.form.get('user_key')
    serial = request.form.get('serial')
    game = request.form.get('game')

    if not user_key or not serial or not game:
        return jsonify({"status": False, "reason": "Missing parameters"})

    # Открываем SQLite
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Ищем ключ
    c.execute("SELECT * FROM keys WHERE key=? AND game=?", (user_key, game))
    row = c.fetchone()

    if not row:
        return jsonify({"status": False, "reason": "Invalid key"})

    # Пример проверки: срок действия
    expiration_timestamp = int(row[3])  # Предположим, 4-й столбец — это expiration (в unix-времени)
    now = int(time.time())

    if expiration_timestamp < now:
        return jsonify({"status": False, "reason": "Key expired"})

    # Генерируем токен и время
    token = generate_token(user_key, serial)
    rng = int(time.time())

    response = {
        "status": True,
        "data": {
            "token": token,
            "rng": rng,
            # Можно добавить другие поля, например ts (timestamp), ms (mod status)
        }
    }

    # (опционально) логируем подключение
    c.execute("INSERT INTO logs (user_key, serial, timestamp) VALUES (?, ?, ?)", (user_key, serial, now))
    conn.commit()
    conn.close()

    return jsonify(response)
# Проверка существующего пользователя
def check_user(username, password):
    conn = get_db_connection()
    # Обязательно установим row_factory, чтобы можно было обращаться по именам полей
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and bcrypt.checkpw(password.encode('utf-8'), row['password']):
        return {'id': row['id'], 'username': row['username']}
    return None

# Регистрация нового пользователя
def add_user(username, password, referral_code=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Хеширование пароля с использованием bcrypt
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    cursor.execute(
        'INSERT INTO users (username, password, referral_code) VALUES (?, ?, ?)',
        (username, hashed_password, referral_code)
    )
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('already_registered.html')
    return render_template('index.html')

@app.route('/already_registered')
def already_registered():
    return render_template('already_registered.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html', user_id=session['user_id'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже залогинен, сообщаем ему, что он уже зарегистрирован
    if 'user_id' in session:
        return render_template('already_registered.html')
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            error = 'Введите логин и пароль'
            return render_template('login.html', error=error, username=username)

        user = check_user(username, password)
        if user:
            session['username'] = user['username']
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            error = 'Неверный логин или пароль'
            return render_template('login.html', error=error, username=username)

    return render_template('login.html')

from flask import flash, redirect, url_for, session

@app.route('/ajax/delete_key/<int:key_id>', methods=['POST'])
def ajax_delete_key(key_id):
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", (session['username'],))
    user = cursor.fetchone()

    if user:
        cursor.execute("DELETE FROM api_keys WHERE id = ? AND user_id = ?", (key_id, user['id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Key deleted successfully'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'Key not found or permission denied'}), 403

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем пользователя
    cursor.execute('SELECT * FROM users WHERE username = ?', (session['username'],))
    user = cursor.fetchone()

    if not user:
        return "User not found", 404

    # Получаем количество созданных ключей
    cursor.execute('SELECT COUNT(*) FROM api_keys WHERE user_id = ?', (user['id'],))
    created_keys = cursor.fetchone()[0]

    # Получаем ключи для отображения
    cursor.execute('SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC', (user['id'],))
    keys = cursor.fetchall()

    conn.close()

    return render_template("profile.html", user=user, created_keys=created_keys, keys=keys)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Если пользователь уже залогинен, он не должен видеть страницу регистрации
    if 'user_id' in session:
        return render_template('already_registered.html')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        referral_code = request.form.get('referral_code', None)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверка существующего логина
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return "Логин уже занят", 400

        # Проверка реферального кода
        cursor.execute("SELECT * FROM referral_codes WHERE code = ? AND is_used = 0", (referral_code,))
        referral = cursor.fetchone()

        if referral:
            add_user(username, password, referral_code)
            cursor.execute("UPDATE referral_codes SET is_used = 1 WHERE code = ?", (referral_code,))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        else:
            conn.close()
            return "Недействительный или использованный реферальный код", 400

    return render_template('registration.html')

@app.route('/create_key', methods=['GET', 'POST'])
def create_key():
    if request.method == 'GET':
        return render_template('create_key.html')  # Просто показываем форму

    if request.method == 'POST':
        user_id = session.get('user_id')
        key_name = os.urandom(5).hex()
        expiration_date = request.form.get('duration')
        device_limit = request.form.get('devices')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO api_keys (user_id, key_name, expiration_date, device_limit, is_active) VALUES (?, ?, ?, ?, ?)",
            (user_id, key_name, expiration_date, device_limit, True)
        )
        conn.commit()
        conn.close()
        print(f"KEY: {key_name}, EXP: {expiration_date}, DEV: {device_limit}")
        return redirect(url_for('gcreate_key', api_key=key_name, duration=expiration_date, devices=device_limit))
        
    return jsonify({"status": "error", "message": "Метод не разрешён"}), 405

@app.route('/gcreate_key')
def gcreate_key():
    api_key = request.args.get('api_key')
    duration = request.args.get('duration')
    devices = request.args.get('devices')

    if not all([api_key, duration, devices]):
        return "Ошибка: не хватает данных.", 400

    return render_template('gcreate_key.html', api_key=api_key, duration=duration, devices=devices)

if __name__ == '__main__':
    app.run(debug=True)