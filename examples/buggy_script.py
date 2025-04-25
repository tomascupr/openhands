"""
A buggy script that demonstrates common Python errors.
"""

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    total = 0
    for num in numbers:
        total = total + num
    return total / len(numbers)

def format_greeting(name, age):
    """Format a greeting message with name and age."""
    # This line has a TypeError: can only concatenate str (not "int") to str
    return "Hello, " + name + "! You are " + age + " years old."

def main():
    # Test the calculate_average function
    numbers = [10, 20, 30, 40, 50]
    average = calculate_average(numbers)
    print(f"The average is: {average}")
    
    # Test the format_greeting function
    name = "Alice"
    age = 30
    greeting = format_greeting(name, age)
    print(greeting)

if __name__ == "__main__":
    main()