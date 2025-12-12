import math_utils as math_utils

def calculate_circle_area():
    radius = float(input("Enter the radius: "))
    return math_utils.circle_area(radius)

def calculate_rectangle_area():
    length = float(input("Enter the length : "))
    width = float(input("Enter the width:  "))
    return math_utils.rectangle_area(length, width)

print("Circle area calculation : ")
print("Area of circle: ",calculate_circle_area())
print("Rectangle area calculation : ")
print("Area of rectangle: ",calculate_rectangle_area())