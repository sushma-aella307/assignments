#exercise 8

import mysql.connector

connection = mysql.connector.connect(

host ="localhost",

user ="root",

passwd ="AellaSushma@2002",

database = "testdb"

)



def insert_multiple_users(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("BEGIN;")
        cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", ("Alice", "alice@example.com"))
        cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", ("Bob", "bob@example.com"))
        connection.commit()  # Commit the transaction
        print("Multiple users inserted successfully.")
    except mysql.connector.Error as err:
        connection.rollback()  # Rollback in case of error
        print(f"Error: {err}. Transaction rolled back.")

insert_multiple_users(connection)
