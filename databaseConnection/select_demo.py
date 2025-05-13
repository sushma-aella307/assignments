import mysql.connector 

dataBase = mysql.connector.connect(
                     host = "localhost",
                     user = "root",
                     passwd = "AellaSushma@2002",
                     database = "pydb" ) 
cursorObject = dataBase.cursor()

query = "SELECT NAME, ROLL FROM STUDENT"
cursorObject.execute(query)

myresult = cursorObject.fetchall()

for x in myresult:
    print(x)

dataBase.close()