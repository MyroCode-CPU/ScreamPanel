import sqlite3

conn = sqlite3.connect('myro_panel.db')
c = conn.cursor()

# Список кодов
referral_codes = [
    "FEZ43F", "MYRIK13", "FIMD31", "YRIKI4232", "ASIROTOP424", "BYMYROCODE",
    "ALLSOFTPUBG", "LOVEALL", "ASIROTIGR", "FIF4WD", "FWEGT3", "F35TRFD",
    "H76TGH", "2FR6YTY", "FIMOZZZZZ", "RYRTU567", "346TRT", "EWTREUYI"
]

# Добавляем коды, если их ещё нет
for code in referral_codes:
    c.execute('INSERT OR IGNORE INTO referral_codes (code, is_used) VALUES (?, ?)', (code, 0))

conn.commit()
conn.close()

print("✅ Реферальные коды успешно добавлены!")
