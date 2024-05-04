"""
Utility functions for working with strings, files, and calculating expenses.
"""


def get_size(contents: str) -> str:
    """
    Get the size of a string in kilobytes (KB) and format it as a string.

    Args:
        contents (str): The string to calculate the size for.

    Preconditions:
        - contents is a valid string

    Side effects:
        None

    Exceptions:
        None

    Returns:
        str: The size of the string in kilobytes, formatted as a string with 2 decimal places.
        guarantees: The returned value will be a non-empty string.
    """
    size = len(contents) / 1024
    return f"{size:.2f} KB"
