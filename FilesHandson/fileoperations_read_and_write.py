#exercise 11

"""list1=["python strings\n","python list\n","python files\n"]
with open("stringslist.txt",'w+') as file:
    for each_line in list1:
        file.write(each_line)

    file.seek(0)
    for line in file:
        print(line)

#exercise 12
with open("stringslist.txt",'r') as file:
    count=0
    for line in file:
        if "python" in line:
            count+=1
    print(count)"""

#exercise 13
import csv
students=[
    ["smith","A"],
    ["tom","C"],
    ["ford","B"]
]
with open("students.csv",'w',newline='') as file:
    writer=csv.writer(file)
    writer.writerows(students)
    
with open("students.csv",'r') as file:
    reader=csv.reader(file)
    for row in reader:
        print(row)