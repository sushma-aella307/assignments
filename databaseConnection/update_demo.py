
from dbconnector import dataBase

cursorObj = dataBase.cursor()


updateQuery = "UPDATE STUDENT SET  name = %s, branch= %s,roll=%s,section=%s,age=%s \
               where sid = %s"

val = ("Tom changed","CSE","24","C","24","101")

cursorObj.execute(updateQuery, val)



dataBase.commit()
dataBase.close()