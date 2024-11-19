import sqlite3

db_name = "dishes.db"
# Connect to the SQLite database
connection = sqlite3.connect(db_name)

# Create a cursor to perform database operations
cursor = connection.cursor()

# Thực hiện truy vấn để lấy tất cả các món ăn
cursor.execute("SELECT * FROM dishes")

# {"sql_query":"INSERT INTO dishes (name, quantity) VALUES ('Phở', 2);"}

# cursor.execute("INSERT INTO dishes (name, quantity) VALUES (?, ?)", ('Bun Dau', 1))

# Lấy tất cả các dòng dữ liệu
result = cursor.fetchall()

print(result)