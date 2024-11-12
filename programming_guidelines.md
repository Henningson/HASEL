# Coding Guidelines for VF Label (WiP Name)

* Code should adhere to PEP8 coding standards.  
* We use black for formating the code.  
* While python is dynamically typed, we want to make it as explicit as possible.
Therefore, we add type-hints whenever possible => for variables, functions, etc.   
* Files should be structured similar to fireflies github.com/Henningson/fireflies


Variables should be defined similar to:
```python
name: str = "Test"
# instead of
name = "Test"
```

Functions should look like:
```python
# With Type Hinting
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

```python
# Without Type Hinting
def greet(name):
    return f"Hello, {name}!"
``` 


Add default parameters whenever applicable:
```python
# Without Type Hinting
def greet(name: str = ""):
    return f"Hello, {name}!"
``` 


## Documenting code
We should document code using Docstrings.  
Adhere to the reStructuredText docstring format.