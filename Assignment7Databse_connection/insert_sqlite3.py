
import sqlite3

def insert_student():
    try:
        # Connect or create a new SQLite database file
        connection = sqlite3.connect("school.db")
        cursor = connection.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL
            )
        """)

        # Insert a new record
        cursor.execute("INSERT INTO students (name, age) VALUES (?, ?)", ("Alice", "21"))
        connection.commit()

        print("Record inserted successfully.")

    except sqlite3.Error as err:
        print(f"SQLite Error: {err}")
    finally:
        connection.close()
        print("Connection closed.")

insert_student()
