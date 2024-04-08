#!/bin/env python

from rich.console import Console
from rich.markdown import Markdown

# Initialize the console
console = Console()

def print_markdown(console: Console, content: str) -> None: #, code_blocks: Optional[dict] = None):
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
    # if code_blocks is None:
    console.print(Markdown(content))
    #     return

    # lines = content.split("\n")
    # code_block_id = 0 if code_blocks is None else 1 + max(code_blocks.keys(), default=0)
    # code_block_open = False
    # code_block_language = ""
    # code_block_content = []
    # regular_content = []

    # for line in lines:
    #     if line.startswith("```") and not code_block_open:
    #         code_block_open = True
    #         code_block_language = line.replace("```", "").strip()
    #         if regular_content:
    #             console.print(Markdown("\n".join(regular_content)))
    #             regular_content = []
    #     elif line.startswith("```") and code_block_open:
    #         code_block_open = False
    #         snippet_text = "\n".join(code_block_content)
    #         if code_blocks is not None:
    #             code_blocks[code_block_id] = snippet_text
    #         formatted_code_block = f"```{code_block_language}\n{snippet_text}\n```"
    #         console.print(f"Block {code_block_id}", style="blue", justify="right")
    #         console.print(Markdown(formatted_code_block))
    #         code_block_id += 1
    #         code_block_content = []
    #         code_block_language = ""
    #     elif code_block_open:
    #         code_block_content.append(line)
    #     else:
    #         regular_content.append(line)

    # if code_block_open:  # uh-oh, the code block was never closed.
    #     console.print(Markdown("\n".join(code_block_content)))
    # elif regular_content:  # If there's any remaining regular content, print it
    #     console.print(Markdown("\n".join(regular_content)))

