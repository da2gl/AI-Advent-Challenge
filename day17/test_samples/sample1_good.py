"""
Sample 1: Well-written Python code
This module demonstrates good coding practices
"""

from typing import List, Optional
import math


class Calculator:
    """A simple calculator class with basic operations"""

    def __init__(self):
        """Initialize calculator with default settings"""
        self.history: List[str] = []
        self.precision = 2

    def add(self, a: float, b: float) -> float:
        """
        Add two numbers

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of a and b
        """
        result = a + b
        self._record_operation(f"{a} + {b} = {result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a"""
        result = a - b
        self._record_operation(f"{a} - {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        result = a * b
        self._record_operation(f"{a} * {b} = {result}")
        return result

    def divide(self, a: float, b: float) -> Optional[float]:
        """
        Divide a by b

        Args:
            a: Numerator
            b: Denominator

        Returns:
            Result of division or None if division by zero

        Raises:
            ValueError: If b is zero
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")

        result = a / b
        self._record_operation(f"{a} / {b} = {result}")
        return result

    def power(self, base: float, exponent: float) -> float:
        """Calculate base raised to exponent"""
        result = math.pow(base, exponent)
        self._record_operation(f"{base} ^ {exponent} = {result}")
        return result

    def get_history(self) -> List[str]:
        """Get calculation history"""
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear calculation history"""
        self.history.clear()

    def _record_operation(self, operation: str) -> None:
        """Record operation in history (private method)"""
        self.history.append(operation)


def calculate_average(numbers: List[float]) -> float:
    """
    Calculate average of a list of numbers

    Args:
        numbers: List of numbers

    Returns:
        Average value
    """
    if not numbers:
        return 0.0

    return sum(numbers) / len(numbers)


def main():
    """Main function to demonstrate calculator usage"""
    calc = Calculator()

    print("Calculator Demo")
    print(f"10 + 5 = {calc.add(10, 5)}")
    print(f"10 - 5 = {calc.subtract(10, 5)}")
    print(f"10 * 5 = {calc.multiply(10, 5)}")
    print(f"10 / 5 = {calc.divide(10, 5)}")

    print("\nHistory:")
    for operation in calc.get_history():
        print(f"  {operation}")


if __name__ == "__main__":
    main()
