

import mysql.connector

connection = mysql.connector.connect(

host ="localhost",

user ="root",

passwd ="AellaSushma@2002",

database = "testdb"

)

# preparing a cursor object

obj = connection.cursor()


sql = "INSERT INTO USERS(name,email) VALUES(%s,%s)"

val = ("smith","smith@example.com")

obj.execute(sql, val)




connection.commit()
connection.close()