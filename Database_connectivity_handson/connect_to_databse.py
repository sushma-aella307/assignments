#exercise 1

import mysql.connector


def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host='localhost',         # MySQL host
            user='root',              # MySQL username
            password='AellaSushma@2002',      # MySQL password
            database='testdb'        # Database name
        )
        print("Successfully connected to the database.")
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
connection=connect_to_db()
