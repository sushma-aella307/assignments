#exercise 7
import mysql.connector

connection = mysql.connector.connect(

host ="localhost",

user ="root",

passwd ="AellaSushma@2002",

database = "testdb"

)


def get_user_by_id(connection, user_id):
    cursor = connection.cursor()
    query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()  # Fetch a single record
    if result:
        print(f"ID: {result[0]}, Name: {result[1]}, Email: {result[2]}")
    else:
        print(f"No user found with ID {user_id}.")

get_user_by_id(connection, 1)