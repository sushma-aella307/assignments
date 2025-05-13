#exercise 8

def squares_generator():

    for i in range(1,11):
        yield i**2

for square in squares_generator():
    print(square)


#exercise 9
def fibonacci_generator(limit=100):
    a,b=0,1
    while a<=limit:
        yield a
        a,b=b,a+b
for num in fibonacci_generator():
    print(num)

#exercise 10
def divisible_generator():
    for i in range(1,51):
        if i%3==0:
            yield i
for num in divisible_generator():
    print(num)

