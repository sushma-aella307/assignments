# importing required libraries

import mysql.connector

connection = mysql.connector.connect(

host ="localhost",

user ="root",

passwd ="AellaSushma@2002",

database = "testdb"

)

# preparing a cursor object

cursorObject = connection.cursor()

# creating table 

usersTable = """CREATE TABLE USERS (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE

				)"""

# table created

obj=cursorObject.execute(usersTable) 
print(obj)

# disconnecting from server

connection.close()