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

def fetch_records():
    connection = connect_to_db()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM students")
            records = cursor.fetchall()

            print("Employee Records:")
            for row in records:
                print(row)
        except mysql.connector.Error as err:
            print(f"Query Error: {err}")
        finally:
            cursor.close()
            connection.close()
            print("Connection closed.")

fetch_records()
