def inout():
    str=input("Enter something: ")
    print("Number of characters:",len(str))
    print("Number of words:",len(str.split()))
    print("number of vowels:",sum(1 for char in str.lower() if char in 'aeiou'))
inout()    