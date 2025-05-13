#exercise 16
import os
file_name="example.txt"
absolute_path=os.path.abspath(file_name)
print("absoulte path is :",absolute_path)


#exercise 17

file_name = "example.txt"

if os.path.exists(file_name):
    with open(file_name, "r") as file:
        content = file.read()
        print("File content:\n", content)
else:
    print(f"File '{file_name}' does not exist.")


