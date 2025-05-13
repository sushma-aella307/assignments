#exercise 11
class CountDown():
    def __init__(self,n):
        self.n=n
    def __iter__(self):
        self.current=self.n
        return self
    def __next__(self):
        if self.current < 1:
            raise StopIteration
        else:
            val=self.current
            self.current -= 1
            return val
        
for num in CountDown(5):
    print(num)

#exercise 12
class EvenNumbers():
    def __init__(self,n):
        self.n=n
    
    def __iter__(self):
        self.current=0
        self.count=0
        return self
    def __next__(self):
        if self.count >= self.n:
            raise StopIteration
        val=self.current
        self.current+=2
        self.count+=1
        return val

 
for val in EvenNumbers(5):
    print(val)