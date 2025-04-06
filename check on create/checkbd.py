import sqlite3
import os

DB_NAME = "myro_panel.db"

def debug_database():
    # Проверка существования базы
    if not os.path.exists(DB_NAME):
        print(f"❌ Файл базы данных '{DB_NAME}' не найден.")
        return

    print(f"🔍 Подключение к базе данных: {DB_NAME}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Получаем список таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if not tables:
        print("⚠️ В базе данных нет таблиц.")
    else:
        print("📋 Список таблиц в базе данных:")
        for table_name in tables:
            print(f"\n  ── 🗂️ Таблица: {table_name[0]} ──")

            # Получаем имена колонок
            try:
                cursor.execute(f"PRAGMA table_info({table_name[0]});")
                columns = [col[1] for col in cursor.fetchall()]
                print("  📌 Колонки:", ", ".join(columns))
            except Exception as e:
                print(f"  ⚠️ Не удалось получить колонки: {e}")

            # Получаем все записи
            try:
                cursor.execute(f"SELECT * FROM {table_name[0]};")
                rows = cursor.fetchall()
                if rows:
                    print(f"  📄 Всего записей: {len(rows)}")
                    for i, row in enumerate(rows, 1):
                        print(f"    {i}. {row}")
                else:
                    print("  (Пусто)")
            except Exception as e:
                print(f"  ⚠️ Ошибка при выборке из {table_name[0]}: {e}")

    conn.close()
    print("\n✅ Проверка базы данных завершена.")

if __name__ == "__main__":
    debug_database()
