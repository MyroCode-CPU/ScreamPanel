import sqlite3
conn = sqlite3.connect('myro_panel.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM referral_codes")
codes = cursor.fetchall()

print("Реферальные коды в базе данных:", codes)

conn.close()
