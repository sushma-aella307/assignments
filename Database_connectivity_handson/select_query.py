import mysql.connector 

connection = mysql.connector.connect(
                     host = "localhost",
                     user = "root",
                     passwd = "AellaSushma@2002",
                     database = "testdb" ) 
obj = connection.cursor()

query = "SELECT id,name  FROM USERS"
obj.execute(query)

myresult = obj.fetchall()

for x in myresult:
    print(x)

connection.close()