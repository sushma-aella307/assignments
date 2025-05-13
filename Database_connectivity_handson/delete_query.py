import mysql.connector

connection = mysql.connector.connect(

host ="localhost",

user ="root",

passwd ="AellaSushma@2002",

database = "testdb"

)

# preparing a cursor object

obj = connection.cursor()



deleteQuery = "DELETE FROM users WHERE ID = %s"

val = ("4",)
obj.execute(deleteQuery, val)




connection.commit()
connection.close()