#exercise 13

def outer_func(func):
    def wrapper(*args,**kwargs):
        print("before function")
        func("args,**kwargs")
        print("after function")
    return wrapper
@outer_func
def display(*args,**kwargs):
    print("hello world")

display()

#exercise 14
import time

def timing_decorator(func):
    def wrapper(*args,**kwargs):
        start = time.time()
        func(*args,**kwargs)
        end=time.time()
        print(f" function took {end - start:.4f} seconds")
    return wrapper

@timing_decorator
def show():
    time.sleep(1)
    print("finished show function")

show()

#exercise 15
def logging_decorator(func):
    def wrapper(*args,**kwargs):
        print(f"calling function : {func.__name__}")
        print(f"arguments: args ={args} kwargs={kwargs}")
        return func(*args,**kwargs)
    return wrapper


@logging_decorator
def add(a,b):
    return a+b

result=add(3,5)
print("result=",result)