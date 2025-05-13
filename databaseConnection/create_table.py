# importing required libraries

import mysql.connector

dataBase = mysql.connector.connect(

host ="localhost",

user ="root",

passwd ="AellaSushma@2002",

database = "pydb"

)

# preparing a cursor object

cursorObject = dataBase.cursor()

# creating table 

studentTable = """CREATE TABLE STUDENT (

                SID INT PRIMARY KEY,
                
				NAME VARCHAR(20) NOT NULL,

				BRANCH VARCHAR(50),

				ROLL INT NOT NULL,

				SECTION VARCHAR(5),

				AGE INT

				)"""

# table created

obj=cursorObject.execute(studentTable) 
print(obj)

# disconnecting from server

dataBase.close()