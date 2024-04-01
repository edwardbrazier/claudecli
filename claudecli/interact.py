#!/bin/env python
"""
This script provides an interactive command-line interface for interacting with the Anthropic AI API.
It allows users to send prompts and receive responses from the AI model.
"""

# import atexit
# import click
# import datetime
# import json
import logging
import os
# import pyperclip
import re
import requests
import sys
# import yaml
import anthropic

# from pathlib import Path
from prompt_toolkit import PromptSession, HTML
# from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.logging import RichHandler
# from rich.markdown import Markdown
from typing import Optional
# from xdg_base_dirs import xdg_config_home

# import constants
# import load
# import printing
import save
from parseaicode import process_assistant_response, ResponseContent, FileData

logger = logging.getLogger("rich")

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    handlers=[
        RichHandler(show_time=False, show_level=False, show_path=False, markup=True)
    ],
)


# Initialize the messages history list
# It's mandatory to pass it at each API call in order to have a conversation
messages = []
# Initialize the console
console = Console()

# def add_markdown_system_message() -> None:
#     """
#     Try to force Claude to always respond with well formatted code blocks and tables if markdown is enabled.
#     """
#     instruction = "Always use code blocks with the appropriate language tags. If asked for a table always format it using Markdown syntax."
#     #messages.append({"role": "system", "content": instruction})

def start_prompt(
    initial_context: str,
    session: PromptSession,
    config: dict,
    copyable_blocks: Optional[dict],
    proxy: dict | None,
    output_dir: str,
    force_overwrite: bool
) -> None:
    """
    Ask the user for input, build the request and perform it.

    Args:
        initial_context (str): The initial context or prompt to provide to the AI model.
        session (PromptSession): The prompt session object for interactive input.
        config (dict): The configuration dictionary containing settings for the API request.
        copyable_blocks (Optional[dict]): A dictionary containing code blocks that can be copied to the clipboard.
        proxy (dict | None): A dictionary containing proxy settings, or None if no proxy is used.
        output_dir (str): The output directory for generated files when using the /o command.
        force_overwrite (bool): Whether to force overwrite of output files if they already exist.

    Preconditions:
        - The `messages` list is initialized and contains the conversation history.
        - The `console` object is initialized for logging and output.

    Side effects:
        - Modifies the `messages` list by appending new messages from the user and the AI model.
        - Prints the AI model's response to the console.
        - Saves the conversation history to a file.
        - Copies code blocks to the clipboard if the user requests it.
        - Writes generated files to the output directory when using the /o command.

    Exceptions:
        - EOFError: Raised when the user enters "/q" to quit the program.
        - KeyboardInterrupt: Raised when the user enters an empty prompt or when certain errors occur during the API request.
        - requests.ConnectionError: Raised when there is a connection error with the API server.
        - requests.Timeout: Raised when the API request times out.

    Returns:
        None
    """

    message = ""

    if config["non_interactive"]:
        message = sys.stdin.read()
    else:
        message = session.prompt(
            HTML(f"<b>[{len(messages)}] >>> </b>")
        )

    if message.lower().strip() == "/q":
        # this is a bit strange to be raising exceptions for normal conditions
        raise EOFError
    if message.lower() == "":
        raise KeyboardInterrupt

    if config["easy_copy"] and message.lower().startswith("/c"):
        # Use regex to find digits after /c or /copy
        match = re.search(r"^/c(?:opy)?\s*(\d+)", message.lower())
        if match:
            block_id = int(match.group(1))
            if block_id in copyable_blocks:
                try:
                    pyperclip.copy(copyable_blocks[block_id])
                    logger.info(f"Copied block {block_id} to clipboard")
                except pyperclip.PyperclipException:
                    logger.error(
                        "Unable to perform the copy operation. Check https://pyperclip.readthedocs.io/en/latest/#not-implemented-error"
                    )
            else:
                logger.error(
                    f"No code block with ID {block_id} available",
                    extra={"highlighter": None},
                )
        elif messages:
            pyperclip.copy(messages[-1]["content"])
            logger.info(f"Copied previous response to clipboard")
        raise KeyboardInterrupt

    if message.lower().startswith("/o"):
        # Remove the "/o" from the message
        message = message[2:].strip()
        write_output =  True
        
        # Add instructions for escaping special characters in XML
        message += "\nMake sure to escape characters correctly inside the XML!"
    else:
        write_output = False

    messages.append({"role": "user", "content": initial_context + message})

    if write_output:
        # Provide a partial assistant message to the model
        messages.append({"role": "assistant", "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"})

    api_key = config["anthropic_api_key"]
    model = config["anthropic_model"]
    base_endpoint = config["anthropic_api_url"]
    
    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0.0,
            messages=messages,
        )
    except requests.ConnectionError:
        logger.error(
            "[red bold]Connection error, try again...", extra={"highlighter": None}
        )
        messages.pop()
        raise KeyboardInterrupt
    except requests.Timeout:
        logger.error(
            "[red bold]Connection timed out, try again...", extra={"highlighter": None}
        )
        messages.pop()
        raise KeyboardInterrupt

    content = response.content

    concatenated_output = ""

    for element in content:
        if element.type == "text":
            t = element.text
            print(t, end='')
            concatenated_output += t
            messages.append({"role": "assistant", "content": t})
            
            if not config["non_interactive"]:
                console.line()
        else:
            print(element)

    if write_output:
        try:
            response_content = ResponseContent(
                content_string=concatenated_output,
                file_data_list=process_assistant_response(concatenated_output)
            )

            if response_content is None:
                console.print("[bold red]Failed to get a response from the AI.[/bold red]")
            else:
                # Write concatenated output to an xml file in output_dir
                concat_file_path = os.path.join(output_dir, "concatenated_output.txt")

                console.print(f"\n[bold green]Writing complete AI output to {concat_file_path}[/bold green]")

                with open(concat_file_path, "w") as f:
                    f.write(response_content.content_string)
                    f.close()

                file_data_list = response_content.file_data_list

                console.print("[bold green]Files included in the result:[/bold green]")

                if len(file_data_list) == 0:
                    console.print("Nil.")
                else:
                    for relative_path, _, changes in file_data_list:
                        console.print(f"[bold magenta]- {relative_path}[/bold magenta]\n[bold green]Changes:[/bold green] {changes}\n")

                    console.print("\n")

                    save.write_files(output_dir, file_data_list, force_overwrite)    

            console.print("[bold green]Done![/bold green]")
        except Exception as e:
            console.print(f"[bold red]Error processing AI response: {e}[/bold red]")

    # match response.status_code:
    #     case 200:
    #         response = r.json()

    #         message_response = {"content": response["content"][0]["text"]}
    #         usage_response = {"prompt_tokens": response["usage"]["input_tokens"], "completion_tokens": response["usage"]["output_tokens"]}

    #         if not config["non_interactive"]:
    #             console.line()
    #         if config["markdown"]:
    #             print.print_markdown(message_response["content"].strip(), copyable_blocks)
    #         else:
    #             print(message_response["content"].strip())
    #         if not config["non_interactive"]:
    #             console.line()

    #         # Update message history and token counters
    #         messages.append({"role": response["role"], "content": message_response["content"]})
    #         prompt_tokens += usage_response["prompt_tokens"]
    #         completion_tokens += usage_response["completion_tokens"]
    #         save.save_history(model, messages, prompt_tokens, completion_tokens)

    #         if config["non_interactive"]:
    #             # In non-interactive mode there is no looping back for a second prompt, you're done.
    #             raise EOFError

    #     case 400:
    #         response = r.json()
    #         if "error" in response:
    #             logger.error(
    #                 f"[red bold]{response['error']}",
    #                 extra={"highlighter": None},
    #             )
    #         logger.error("[red bold]Invalid request", extra={"highlighter": None})
    #         raise EOFError

    #     case 401:
    #         logger.error("[red bold]Invalid API Key", extra={"highlighter": None})
    #         raise EOFError

    #     case 429:
    #         logger.error(
    #             "[red bold]Rate limit or maximum monthly limit exceeded",
    #             extra={"highlighter": None},
    #         )
    #         messages.pop()
    #         raise KeyboardInterrupt

    #     case 500:
    #         logger.error(
    #             "[red bold]Internal server error",
    #             extra={"highlighter": None},
    #         )
    #         messages.pop()
    #         raise KeyboardInterrupt

    #     case 502 | 503:
    #         logger.error(
    #             "[red bold]The server seems to be overloaded, try again",
    #             extra={"highlighter": None},
    #         )
    #         messages.pop()
    #         raise KeyboardInterrupt

    #     case _:
    #         logger.error(
    #             f"[red bold]Unknown error, status code {r.status_code}",
    #             extra={"highlighter": None},
    #         )
    #         logger.error(r.json(), extra={"highlighter": None})
    #         raise EOFError



