
import mysql.connector 

connection = mysql.connector.connect(
                     host = "localhost",
                     user = "root",
                     passwd = "AellaSushma@2002",
                     database = "testdb" ) 
obj = connection.cursor()



updateQuery = "UPDATE users SET  name = %s where id = %s"

val = ("jonn","1")

obj.execute(updateQuery, val)



connection.commit()
connection.close()