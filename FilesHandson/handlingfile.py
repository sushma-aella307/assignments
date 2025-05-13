#exercise 7
try:
    with open("items.txt",'r') as file:
        content=file.read()
        print(content)
except FileNotFoundError as e:
    print(e)
 

# with open("items.txt",'r') as file:
#     content=file.read()
#     print(content)
