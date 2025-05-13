from dbconnector import dataBase

cursorObj = dataBase.cursor()

deleteQuery = "DELETE FROM STUDENT WHERE SID = %s"

val = ("101",)

cursorObj.execute(deleteQuery, val)




dataBase.commit()
dataBase.close()