#!/bin/env python

from rich.console import Console
from rich.markdown import Markdown

# Initialize the console
console = Console()


def print_markdown(
    console: Console, content: str
) -> None: 
    """
    Print markdown formatted text to the terminal.

    Args:
        console (Console): The Rich console instance to use for printing.
        content (str): The markdown content to print.

    Preconditions:
        - The `content` argument must be a valid string containing markdown.

    Side effects:
        - Prints the markdown content to the console.

    Exceptions:
        None.

    Returns:
        None.
    """
    console.print(Markdown(content))