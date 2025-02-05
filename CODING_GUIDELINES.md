# Python Library Coding Guidelines

This document provides guidelines to ensure the code in our library is consistent, clean, and easy to maintain. All contributors should follow these rules when writing code.

---

## 1. Code Style: PEP8

We follow the [PEP8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code, which includes guidelines on indentation, naming conventions, imports, and more. Please refer to the PEP8 document for details on style requirements.

### Example

```python
# PEP8-compliant example
def add_numbers(x: int, y: int) -> int:
    """Adds two numbers and returns the result."""
    return x + y
```

## 2. Code Formatting: Black

We use the [Black](https://black.readthedocs.io/en/stable/) formatter to ensure consistent formatting. Black should be run on every file before committing. To streamline this, set up "Format on Save" in your editor so that Black formats the code automatically.

### Example of Formatting with Black

Black enforces consistent line lengths and styles:

```python
# Before Black formatting
def long_function_name(
    var_one, var_two, var_three, var_four
): return var_one + var_two + var_three + var_four

# After Black formatting
def long_function_name(var_one, var_two, var_three, var_four):
    return var_one + var_two + var_three + var_four
```

---

## 3. Documentation Style: ReStructuredText (reST)

All documentation should be written in [ReStructuredText](https://docutils.sourceforge.io/rst.html) style. Every module, class, and function should have a docstring to explain its purpose and usage. 

### Example of a ReStructuredText Docstring

```python
def multiply_numbers(x: int, y: int) -> int:
    """
    Multiply two integers.

    :param x: The first integer
    :type x: int
    :param y: The second integer
    :type y: int
    :return: The product of x and y
    :rtype: int
    """
    return x * y
```

---

## 4. Explicit Code and Type Hinting

Our code should be as explicit as possible to improve readability and maintainability. **Type hinting** is required for every function parameter, return type, and variable.

### Example of Explicit Code and Type Hinting

```python
# Example function with type hints
def process_data(data: list[str], multiplier: int) -> list[str]:
    """Processes a list of strings by repeating each string a specified number of times.

    :param data: A list of strings to process
    :type data: list[str]
    :param multiplier: The number of times to repeat each string
    :type multiplier: int
    :return: A list with each string repeated
    :rtype: list[str]
    """
    result: list[str] = []
    for item in data:
        result.append(item * multiplier)
    return result
```

In this example, `data` and `multiplier` parameters, the return type, and the `result` variable are all explicitly typed.

---

## Summary

1. **PEP8**: Adhere to PEP8 guidelines.
2. **Black Formatting**: Use Black for consistent formatting, with "Format on Save" enabled.
3. **Documentation**: Write docstrings in ReStructuredText format.
4. **Type Hinting**: Type hint all variables and functions to ensure explicit, readable code.

Following these guidelines will help keep our codebase clean, consistent, and maintainable. Happy coding!
```

This is ready to be pasted into a markdown file. Let me know if you need further customization!
