#exercise 9

import mysql.connector 

connection = mysql.connector.connect(
                     host = "localhost",
                     user = "root",
                     passwd = "AellaSushma@2002",
                     database = "testdb" ) 
obj = connection.cursor()

def close_connection(connection):
    if connection.is_connected():
        connection.close()
        print("Database connection closed.")

close_connection(connection)