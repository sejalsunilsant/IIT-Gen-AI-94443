import math

def circle_area(radius):
    if radius < 0:
        raise ValueError("Radius cannot be negative.")
    return math.pi * radius ** 2

def rectangle_area(length, width):
    if length < 0 or width < 0:
        raise ValueError("Length and width cannot be negative.")
    return length * width

if __name__ == "__main__":
    print("Circle area with radius 5:", circle_area(5))
    print("Rectangle area with length 4 and width 6:", rectangle_area(4, 6))