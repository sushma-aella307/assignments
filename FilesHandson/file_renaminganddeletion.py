#exercise 14
import os
old_name="student.csv"
new_name="changed.csv"
if os.path.exists(old_name):
    os.rename(old_name,new_name)
    print(f"renameed {old_name} to {new_name}")
else:
    print(f"file {old_name} does not exists")


#exercise 15
file_delete="rough.txt"
if os.path.exists(file_delete):
    os.remove(file_delete)
    print(f" file {file_delete} is deleted")
else:
    print(f"file {file_delete} does not exists")
