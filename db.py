import sqlite3
try:
    # Connect to SQLite Database and create a cursor
    sqliteConnection = sqlite3.connect('userdata.db')
    cursor = sqliteConnection.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios ( id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE, password TEXT NOT NULL, role TEXT DEFAULT 'cliente' )")

    print("Table is ready")

except sqlite3.Error as error:
    print('Error occurred -', error)

finally:
    # Ensure the database connection is closed
    if sqliteConnection:
        sqliteConnection.close()
        print('SQLite Connection closed')
