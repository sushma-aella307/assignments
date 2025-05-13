#exercise 6
evens={x for x in range(1,21) if x%2==0}
print(evens)


#exercise 7
string="set comprehension unique vowels"
vowels={char for char in string.lower() if char in "aeiou"}
print(vowels)
