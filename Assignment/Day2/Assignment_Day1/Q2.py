def EvenOdd(num):
    if num % 2 == 0:
        return "Even"
    else:
        return "Odd"
list_of_numbers =input("Enter numbers separated by spaces: ").split()


print("Number of Even numbers:")
even_count = sum(1 for number in list_of_numbers if EvenOdd(int(number)) == "Even")
print(even_count)
print("Number of Odd numbers:")
odd_count = sum(1 for number in list_of_numbers if EvenOdd(int(number)) == "Odd")
print(odd_count)
    