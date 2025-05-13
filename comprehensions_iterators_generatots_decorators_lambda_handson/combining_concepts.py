#exercise 20
evens_squares=list(map(lambda a : a**2,{x for x in range(1,21) if x%2==0}))
print(evens_squares)

#exercise 21

total=sum(x**2 for x in range(1,6))
print(total)

#exercise 22

def outer_func(func):
    def wrapper(*args,**kwargs):
        print("we are calling a function called:",func.__name__)
        return func(*args,**kwargs)
    return wrapper

@outer_func
def squares_generator(n):
    for i in range(1,n+1):
        yield i**2

for square in squares_generator(5):
    print(square)
