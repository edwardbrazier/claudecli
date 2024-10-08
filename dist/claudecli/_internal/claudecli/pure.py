"""
Utility functions for working with strings, files, and calculating expenses.
"""

from claudecli.parseaicode import Usage
from claudecli.constants import opus, sonnet, haiku


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


def calculate_cost(usage: Usage, model_name: str) -> float:
    """
    Calculate the cost of a message based on the token usage and model name.

    Args:
        usage (Usage): The token usage for the message.
        model_name (str): The short name of the model used (e.g., "haiku", "sonnet", "opus").

    Preconditions:
        - usage is a valid Usage object.
        - model_name is one of "haiku", "sonnet", or "opus".

    Side effects:
        None

    Exceptions:
        None

    Returns:
        float: The cost of the message in USD.
        guarantees: The returned value will be a non-negative float.
    """
    assert isinstance(usage, Usage), "usage must be a Usage object"
    assert model_name in [
        haiku,
        sonnet,
        opus,
    ], "model_name must be one of 'haiku', 'sonnet', or 'opus'"

    pricing = {haiku: (0.25, 0.30, 0.03,  1.25), sonnet: (3.0, 3.75, 0.30, 15.0), opus: (15.0, 18.75, 1.50, 75.0)}

    input_cost_per_million, cache_creation_cost_per_million, cache_read_cost_per_million, output_cost_per_million = \
        pricing[model_name]

    input_cost = usage.input_tokens_regular * input_cost_per_million / 1_000_000
    cache_creation_cost = usage.cache_creation_input_tokens * cache_creation_cost_per_million / 1_000_000
    cache_read_cost = usage.cache_read_input_tokens * cache_read_cost_per_million / 1_000_000
    output_cost = usage.output_tokens * output_cost_per_million / 1_000_000

    total_cost = input_cost + cache_creation_cost + cache_read_cost + output_cost
    return total_cost


def format_cost(usage: Usage, model_name: str) -> str:
    """
    Format the cost and token usage into a colored string.

    Args:
        usage (Usage): The token usage for the message.
        model_name (str): The short name of the model used (e.g., "haiku", "sonnet", "opus").

    Preconditions:
        - usage is a valid Usage object.
        - model_name is one of "haiku", "sonnet", or "opus".

    Side effects:
        None

    Exceptions:
        None

    Returns:
        str: The formatted cost string.
        guarantees: The returned value will be a non-empty string.
    """
    assert isinstance(usage, Usage), "usage must be a Usage object"
    assert model_name in [
        haiku,
        sonnet,
        opus,
    ], "model_name must be one of 'haiku', 'sonnet', or 'opus'"

    cost = calculate_cost(usage, model_name)
    return (f"[bold green]Tokens used in this message:[/bold green] \n"
            f"Regular Input - {usage.input_tokens_regular}; \n"
            f"Cache Creation Input - {usage.cache_creation_input_tokens}; \n"
            f"Cache Read Input - {usage.cache_read_input_tokens}; \n"
            f"Output - {usage.output_tokens} \n"
            f"[bold green]Cost:[/bold green] ${cost:.4f} USD")
