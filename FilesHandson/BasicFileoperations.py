#exercise 1
with open("example.txt",'w') as file:
    file.write("Hello World")

#exercise 2
with open("example.txt",'r') as file:
    content=file.read()
    print(content)
    
#exercise 3
with open("example.txt",'a') as file:
    file.write("this is a new line")

#exercise 4
file=open("example.txt",'r')
content=file.read()
print(content)
file.close()