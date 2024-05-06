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
        code_blocks (Optional[dict]): An optional dictionary to store code blocks.

    Preconditions:
        - The `content` argument must be a valid string containing markdown.
        - If `code_blocks` is provided, it must be a dictionary.

    Side effects:
        - Prints the markdown content to the console.
        - If `code_blocks` is provided, it will be modified to store any code blocks found in the content.

    Exceptions:
        None.

    Returns:
        None.
    """
    console.print(Markdown(content))