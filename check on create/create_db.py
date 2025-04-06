import sqlite3
import os

DB_NAME = "myro_panel.db"

def initialize_database():
    # Проверяем, существует ли файл базы данных
    db_exists = os.path.exists(DB_NAME)

    # Подключаемся к БД
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("🚀 Инициализация базы данных...")

    # 1️⃣ Создание таблицы реферальных кодов (она нужна первой)
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS referral_codes (
            code TEXT PRIMARY KEY,
            is_used INTEGER DEFAULT 0 CHECK (is_used IN (0,1)),  -- 0 = не использован, 1 = использован
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ Таблица referral_codes создана.")

    # 2️⃣ Создание таблицы пользователей (зависит от referral_codes)
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
            referral_code TEXT,
            registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referral_code) REFERENCES referral_codes(code)
        )
    ''')
    print("✅ Таблица users создана.")


    # 3️⃣ Создание таблицы API-ключей (зависит от users)
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key_name TEXT UNIQUE NOT NULL,
            expiration_date TEXT NOT NULL,
            device_limit INTEGER NOT NULL CHECK (device_limit >= 1),
            is_active INTEGER DEFAULT 1 CHECK (is_active IN (0,1)),  
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    ''')
    print("✅ Таблица api_keys создана.")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_key TEXT NOT NULL,
            serial TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        );
    ''')
    print("✅ Таблица logs создана.")
    # 4️⃣ Создание индексов для оптимизации запросов
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys (user_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_referral_codes_code ON referral_codes (code);')
    print("⚡ Оптимизация базы данных завершена.")

    # 5️⃣ Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()

    if db_exists:
        print("🔄 База данных обновлена.")
    else:
        print("🎉 База данных успешно инициализирована.")

if __name__ == "__main__":
    initialize_database()
