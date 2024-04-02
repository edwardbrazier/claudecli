"""
Utility functions for working with strings, files, and calculating expenses.
"""

# def calculate_expense(
#     prompt_tokens: int,
#     completion_tokens: int,
#     prompt_pricing: float,
#     completion_pricing: float,
# ) -> float:
#     """
#     Calculate the expense for a given number of tokens and pricing rates.

#     Args:
#         prompt_tokens (int): The number of tokens in the prompt.
#         completion_tokens (int): The number of tokens in the completion.
#         prompt_pricing (float): The pricing rate for prompt tokens.
#         completion_pricing (float): The pricing rate for completion tokens.

#     Preconditions:
#         - prompt_tokens >= 0
#         - completion_tokens >= 0
#         - prompt_pricing >= 0
#         - completion_pricing >= 0

#     Side effects:
#         None

#     Exceptions:
#         None

#     Returns:
#         float: The calculated expense, rounded to 6 decimal places.
#         guarantees: The returned value will be non-negative.
#     """
#     expense = ((prompt_tokens / 1000) * prompt_pricing) + (
#         (completion_tokens / 1000) * completion_pricing
#     )

#     # Format to display in decimal notation rounded to 6 decimals
#     expense = "{:.6f}".format(round(expense, 6))

#     return expense


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