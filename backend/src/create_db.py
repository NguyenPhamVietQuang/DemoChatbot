import sqlite3

def setup_database(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            quantity INTEGER NOT NULL
        )
    ''')
    # Thêm một số món ăn mẫu
    dishes = [
        ('Phở', 50),
        ('Bún Chả', 30),
        ('Bánh Mì', 100),
        ('Cơm Tấm', 40),
        ('Gỏi Cuốn', 60)
    ]
    for dish in dishes:
        try:
            cursor.execute('INSERT INTO dishes (name, quantity) VALUES (?, ?)', dish)
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

setup_database('dishes.db')
