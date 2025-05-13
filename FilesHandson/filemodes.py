#exercise 5

list_lines=["hello\n","world\n","hi"]
with open("strings.txt",'w') as file:

    file.writelines(list_lines)

#exercise 6
with open("strings.txt",'r') as file:
    # content=file.readlines() no need
    for each_line in file:
        print(each_line)

#exercise 7
with open("binary_data.txt",'rb') as file:
    content=file.read()
    print(content)


