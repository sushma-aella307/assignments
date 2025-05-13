#exercise 9
with open("example.txt",'w') as file:
    file.write("over written")

#exercise 10
with open("strings.txt",'r') as file:
    for line in file:
        print(line)
