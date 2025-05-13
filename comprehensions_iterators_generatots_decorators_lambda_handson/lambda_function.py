#exercise 16
f=lambda a,b: a+b
print(f(2,3))

#exercise 17
f=lambda a,b: a if a>b else b
print("maximum value is:",f(4,5))

#exercise 18

l=[1,2,3,5,6,4,6,7,8]
evens=list(filter(lambda x: x%2==0,l))
print(evens)

#exercise 19
l=[1,2,3,4,5]
squares=list(map(lambda x: x**2,l))
print(squares)

